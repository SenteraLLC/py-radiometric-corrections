# flake8: noqa
"""
Define criteria for identifying sensors and their correction settings.

Usage; add dictionary entries of the following format:
{
    'criteria': {  # required
        exif key: substring of exif value,
        ...
    },
    'ignore_criteria': {  # optional. Images that meet criteria and ignore_criteria will be ignored and will not throw errors
        exif key: substring of exif value,
        ...
    },
    'settings': {  # required
        'sensor': sensor name as string,
        'cal_in_path': boolean indicating whether or not calibration images
                       can be identified based on a substring in their paths
                       ex: calibration images are all named CAL_...tif
                       and non-calibration images are all named IMG_...tif,
        'independent_ils': boolean indicating whether or not image metadata
                           includes band-specific SunSensor information. If
                           False, clear band ILS data will be used instead,
    },
    'bands': an optional list of tuples for sensors that describe multiple
             bands in a single image.
             format: (band name, band math coefficients, band metadata position)
             band name: determines name of band output folder
             band math coefficients: pixel = red*c0 + green*c1 + blue*c2
             band metadata position: index of band specific metadata
}
"""

sensor_defs = [
    {
        "criteria": {
            "Image Make": "Sentera",
            "Image Model": "2102",
            "EXIF LensModel": "5.4mm-0001_0016",
        },
        "settings": {
            "sensor": "D4K_NarrowNDRE",
            "cal_in_path": False,
            "independent_ils": False,
        },
        "bands": [("rededge", [1.0, 0.0, -0.956], 0), ("nir", [-0.341, 0.0, 2.426], 2)],
    },
    {
        "criteria": {
            "Image Make": "Sentera",
            "Image Model": "2102",
            "EXIF LensModel": "5.4mm-0001_0015",
        },
        "settings": {
            "sensor": "D4K_NarrowNDVI",
            "cal_in_path": False,
            "independent_ils": False,
        },
        "bands": [("red", [1.0, 0.0, -0.966], 0), ("nir", [-0.286, 0.0, 4.350], 2)],
    },
    {
        "criteria": {
            "Image Make": "Sentera",
            "Image Model": "2102",
            "EXIF LensModel": "25.0mm-0001_0008",
        },
        "settings": {
            "sensor": "D4K_RGB",
            "cal_in_path": False,
            "independent_ils": False,
        },
        "bands": [
            ("red", [1.0, 0.0, 0.0], 0),
            ("green", [0.0, 1.0, 0.0], 1),
            ("blue", [0.0, 0.0, 1.0], 2),
        ],
    },
    {
        "criteria": {
            "Image Make": "Sentera",
            "Image Model": "2102",
            "EXIF LensModel": "5.4mm-0001_0014",
        },
        "settings": {
            "sensor": "D4K_NarrowRGB",
            "cal_in_path": False,
            "independent_ils": False,
        },
        "bands": [
            ("red", [1.0, 0.0, 0.0], 0),
            ("green", [0.0, 1.0, 0.0], 1),
            ("blue", [0.0, 0.0, 1.0], 2),
        ],
    },
    {
        "criteria": {"Image Make": "Sentera", "Image Model": "21214"},
        "ignore_criteria": {"Image Model": "20MP-ERS"},  # RGB
        "settings": {
            "sensor": "6x",
            "cal_in_path": True,
            "independent_ils": True,
        },
    },
    {
        "criteria": {"Image Make": "Sentera", "Image Model": "21216"},
        "ignore_criteria": {"Image Model": [
            "82KP", # LWIR
            "20MP-ERS", #RGB
        ]},  
        "settings": {
            "sensor": "6x_thermal",
            "cal_in_path": True,
            "independent_ils": True,
        },
    },
]
