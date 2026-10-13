"""Dataset-related functions for reviewing input imagery."""

import json
import logging
from datetime import timedelta

import numpy as np
import pandas as pd
from imgparse import MetadataParser, ParsingError

from imgcorrect import io
from imgcorrect.corrections import _select_calibration_set
from imgcorrect.detect_panel import detect_aruco_markers

logger = logging.getLogger(__name__)


def check_calibration_panels(input_path, calibration_id="CAL"):
    """Determine if calibration panel images are present in the given input path and the aruco marker is readable.

    Args:
        input_path (str): Path to the directory containing multispectral images.
        calibration_id (str): Identifier for calibration panel images. Default is "CAL".

    Returns:
        bool: True if calibration panel images are detected, False otherwise.
    """
    image_df = io.create_image_df(input_path, input_path)
    image_df["EXIF"] = image_df.apply(
        lambda row: MetadataParser(row.image_path).exif_data, axis=1
    )
    image_df = io.apply_sensor_settings(image_df)
    cal_df, non_cal_df = io.create_cal_df(image_df, calibration_id)

    if cal_df.empty:
        return False
    else:
        return True


def calibration_ils_check(cal_df, image_df):
    """Check the ILS of calibration panels compared to the flight images.

    Args:
        cal_df (pd.DataFrame): DataFrame containing calibration panel images.
        image_df (pd.DataFrame): DataFrame containing all images.

    Returns:
        list: A list of DataFrames with ILS check results for each calibration set.
    """
    group_ids = (
        cal_df["timestamp"] > (cal_df["timestamp"].shift() + timedelta(seconds=10))
    ).cumsum()
    calibration_sets = cal_df.groupby(group_ids)

    band_avg_ils = image_df.groupby("band").ILS.mean().reset_index()

    _, _, selected_group_id = _select_calibration_set(cal_df, image_df)

    cal_panel_check_results = []

    for set_id, cal_set in calibration_sets:
        set_df = cal_set.groupby("band").ILS.mean().reset_index()
        set_df["set_id"] = set_id
        set_df["ils_difference"] = (band_avg_ils["ILS"] - set_df["ILS"]).abs() / (
            (band_avg_ils["ILS"] + set_df["ILS"]) / 2
        )
        set_df[["ILS", "ils_difference"]] = set_df[["ILS", "ils_difference"]].round(3)

        set_df["selected_set"] = set_id == selected_group_id

        cal_panel_check_results.append(
            set_df[["set_id", "selected_set", "band", "ILS", "ils_difference"]]
        )

    return cal_panel_check_results


def _numpy_kmeans_2(points, max_iter=100, tolerance=1e-8):
    """Fit two centers with NumPy using first-point/farthest-point initialization."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
        raise ValueError("At least two two-dimensional samples are required.")
    if not np.isfinite(points).all():
        raise ValueError("Samples must contain only finite values.")
    if max_iter < 1 or not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError(
            "max_iter must be positive and tolerance finite and nonnegative."
        )

    first = points[0]
    second = points[np.argmax(np.sum((points - first) ** 2, axis=1))]
    centers = np.vstack((first, second))

    for _ in range(max_iter):
        distances = np.sum((points[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        groups = np.argmin(distances, axis=1)
        new_centers = centers.copy()
        for group in range(2):
            members = points[groups == group]
            if len(members):
                new_centers[group] = members.mean(axis=0)
            else:
                assigned = distances[np.arange(len(points)), groups]
                new_centers[group] = points[np.argmax(assigned)]

        converged = np.allclose(new_centers, centers, atol=tolerance, rtol=0)
        centers = new_centers
        if converged:
            break

    distances = np.sum((points[:, None, :] - centers[None, :, :]) ** 2, axis=2)
    return np.argmin(distances, axis=1), centers


def _circular_yaw_group(yaw_series, n_groups=2, labels=None, threshold_deg=20):
    """Find two dominant yaw directions using one NumPy circular K-means fit.

    Args:
        yaw_series (pd.Series): Yaw angles in degrees; invalid values remain missing.
        n_groups (int): Must be 2 for the opposing survey directions.
        labels (list, optional): Two labels, defaulting to FlightDir1 and FlightDir2.
        threshold_deg (float): Maximum survey-heading deviation, between 0 and 90.

    Returns:
        pd.Categorical: Direction labels or Transect/Other for off-axis headings.
            Labels follow ascending normalized center angles, not flight order.
    """
    if n_groups != 2:
        raise ValueError("Circular K-means requires exactly two direction groups.")
    if labels is None:
        labels = ["FlightDir1", "FlightDir2"]
    if len(labels) != 2 or len(set(labels)) != 2 or "Transect/Other" in labels:
        raise ValueError("Provide two distinct labels other than Transect/Other.")
    if not 0 < threshold_deg < 90:
        raise ValueError("threshold_deg must be between 0 and 90 degrees.")

    yaw = pd.to_numeric(yaw_series, errors="coerce").to_numpy(
        dtype=float, na_value=np.nan
    )
    valid = np.isfinite(yaw)
    values = yaw[valid] % 360
    group_codes = np.full(len(yaw), -1, dtype=int)
    categories = pd.Index(list(labels) + ["Transect/Other"])

    if len(np.unique(values)) < 2:
        group_codes[valid] = 0
        return pd.Categorical.from_codes(group_codes, categories=categories)

    radians = np.radians(values)
    points = np.column_stack((np.cos(radians), np.sin(radians)))
    _, centers_xy = _numpy_kmeans_2(points)
    centers = np.sort(np.degrees(np.arctan2(centers_xy[:, 1], centers_xy[:, 0])) % 360)
    distances = np.abs((values[:, None] - centers + 180) % 360 - 180)
    groups = distances.argmin(axis=1)
    deviation = distances[np.arange(len(values)), groups]
    group_codes[valid] = np.where(deviation > threshold_deg, 2, groups)

    return pd.Categorical.from_codes(group_codes, categories=categories)


def flight_ils_variance_check(image_df, group_by_direction=True):
    """Check variance of ILS values across flight images and return coefficient of variation (CV) for each band.

    Args:
        image_df (pd.DataFrame): DataFrame containing all flight images.
        group_by_direction (bool): Group by two learned yaw directions, excluding
        invalid headings and headings more than 20 degrees from either center.

    Returns:
        pd.DataFrame: A DataFrame containing the CV for each band.
    """
    if group_by_direction:
        image_df["yaw_group"] = _circular_yaw_group(image_df["yaw"])
        survey_df = image_df.loc[image_df["yaw_group"] != "Transect/Other"]
        yaw_group_stats_frames = []
        for group_id, group in survey_df.groupby("yaw_group", observed=True):
            group_stats = group.groupby("band").ILS.agg(["mean", "std"]).reset_index()
            group_stats["set_id"] = group_id
            group_stats["cv"] = group_stats["std"] / group_stats["mean"]
            yaw_group_stats_frames.append(group_stats[["band", "cv"]])

        if not yaw_group_stats_frames:
            return pd.DataFrame(columns=["band", "cv"])
        yaw_group_stats = pd.concat(yaw_group_stats_frames, ignore_index=True)

        band_stats = yaw_group_stats.groupby("band").cv.mean().reset_index()
        band_stats[["cv"]] = band_stats[["cv"]].round(3)

    else:
        band_stats = image_df.groupby("band").ILS.agg(["mean", "std"]).reset_index()
        band_stats["cv"] = band_stats["std"] / band_stats["mean"]
        band_stats[["cv"]] = band_stats[["cv"]].round(3)

    return band_stats[["band", "cv"]]


def _to_jsonable(value):
    """Recursively convert pandas/numpy objects into JSON-serializable values."""
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_list()
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def multispectral_ils_check(input_path, calibration_id="CAL", output_file_path=None):
    """Perform multispectral ILS check on the images in the given input path.

    Args:
        input_path (str): Path to the directory containing flight images.
        calibration_id (str): Identifier for calibration panel images. Default is "CAL".
        output_file_path (str, optional): Path to save the JSON results to a file. If None, results are not saved. Output file must have a .json extension.

    Returns:
        dict: A dictionary containing the results of the calibration panel detection, calibration panel ILS check, and flight variance check.
    """
    if output_file_path and not output_file_path.endswith(".json"):
        raise ValueError("Output file path must have a .json extension.")
    image_df = io.create_image_df(input_path, input_path)
    image_df["EXIF"] = image_df.apply(
        lambda row: MetadataParser(row.image_path).exif_data, axis=1
    )
    image_df = io.apply_sensor_settings(image_df)

    def _safe_ils(image_path):
        """Return first ILS value, or None when metadata cannot be parsed."""
        try:
            ils_values = MetadataParser(image_path).ils()
            return ils_values[0] if ils_values else None
        except ParsingError:
            return None

    image_df["ILS"] = image_df["image_path"].apply(_safe_ils)
    image_df["yaw"] = image_df.apply(
        lambda row: MetadataParser(row["image_path"]).rotation()[2], axis=1
    )
    image_df["timestamp"] = image_df.apply(
        lambda row: MetadataParser(row.image_path).timestamp(), axis=1
    )
    image_df = image_df.set_index("timestamp", drop=False).sort_index()

    cal_df, non_cal_df = io.create_cal_df(image_df, calibration_id)

    if image_df["ILS"].isna().all():
        logger.warning("No valid ILS values found in the images, skipping ILS check.")
        panel_ils_results = None
        flight_check_results = None
    else:
        panel_ils_results = (
            None if cal_df.empty else calibration_ils_check(cal_df, non_cal_df)
        )
        if cal_df.empty:
            logger.warning("No calibration panel images found, skipping ILS check.")
        flight_check_results = flight_ils_variance_check(non_cal_df)

    panel_detection_results = detect_aruco_markers(cal_df) if not cal_df.empty else None

    results = {
        "calibration_panel_detection": panel_detection_results,
        "calibration_panel_ils_check": panel_ils_results,
        "flight_variance_check": flight_check_results,
    }

    jsonable_results = _to_jsonable(results)

    if output_file_path:
        with open(output_file_path, "w") as f:
            json.dump(jsonable_results, f, indent=4)

    return jsonable_results
