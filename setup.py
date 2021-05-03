"""Library to perform various corrections on native 6X imagery."""

import re
import setuptools

VERSIONFILE = "correct6x/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setuptools.setup(
    name="py6x",
    version=verstr,
    description="Correction library for Sentera 6X imagery.",
    packages=setuptools.find_packages(),
    install_requires=[
        "Pillow",
        "numpy",
        "tifffile",
        "pandas",
        "tqdm",
        "opencv-contrib-python",
        "imgparse @ git+https://github.com/SenteraLLC/py-image-metadata-parser.git@v1.9.2",
        "imgreg @ git+https://github.com/SenteraLLC/py-image-registration.git@v0.1.0"
    ],
    extras_require={
        "dev": ["pytest", "sphinx_rtd_theme", "pre-commit", "m2r", "sphinx"],
    },
)
