import imgcorrect

def test_6x_cal_ils():
    imgcorrect.correct_images(
        "tests/6x_images/",
        "CAL",
        "tests/output/6x_cal_ils/",
        False,
        False,
        False,
        "exiftool",
        False
    )

def test_6x_cal_ils_u16():
    imgcorrect.correct_images(
        "tests/6x_images/",
        "CAL",
        "tests/output/6x_cal_ils_u16/",
        False,
        False,
        False,
        "exiftool",
        True
    )

def test_6x_no_ils_no_cal_u16():
    imgcorrect.correct_images(
        "tests/6x_images/",
        "CAL",
        "tests/output/6x_no_ils_no_cal_u16/",
        True,
        True,
        False,
        "exiftool",
        True
    )

def test_d4k_ils():
    imgcorrect.correct_images(
        "tests/d4k_images/",
        "CAL",
        "tests/output/d4k_ils/",
        False,
        True,
        False,
        "exiftool",
        False
    )