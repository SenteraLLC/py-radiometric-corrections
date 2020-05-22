import bisect

BLUE_PANEL_COEFFICIENT = 0.1059
GREEN_PANEL_COEFFICIENT = 0.1054
RED_PANEL_COEFFICIENT = 0.1052
RED_EDGE_PANEL_COEFFICIENT = 0.1052
NEAR_INFRARED_COEFFICIENT = 0.1055

BAND_COEFFS = {
    'blue': BLUE_PANEL_COEFFICIENT,
    'green': GREEN_PANEL_COEFFICIENT,
    'red': RED_PANEL_COEFFICIENT,
    'red edge': RED_EDGE_PANEL_COEFFICIENT,
    'nir': NEAR_INFRARED_COEFFICIENT
}

def take_closest_image(mean_dn_df):
    band_correction_dn_index = bisect.bisect_left(mean_dn_df.loc[:,'mean_reflectance'], 2048)
    optimal_mean_dn_index = band_correction_dn_index - 1
    return optimal_mean_dn_index


# I need mean_dn_values from detect_panel.py as a data frame with additional columns of autoexposure and iso/100.
def ae_normalize_mean_dn(optimal_mean_dn, autoexposure):
    normalized_mean_dn = optimal_mean_dn / autoexposure
    return normalized_mean_dn


def empirical_line_function(normalized_mean_dn, band):
    slope_coefficient = normalized_mean_dn / BAND_COEFFS[band]
    return slope_coefficient