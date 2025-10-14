"""
Evaluation configuration and constants
"""

from pathlib import Path

# Paths
EVALS_DIR = Path(__file__).parent
FIXTURES_DIR = EVALS_DIR / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
RESULTS_DIR = EVALS_DIR / "results"

# Ensure directories exist
FIXTURES_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Expected JSON schema for photo analysis
EXPECTED_JSON_SCHEMA = {
    "overall_impression": str,
    "concise_bullet_points": {
        "technical": str,
        "artistic": str,
        "best_practice": str,
        "next_step": str,
    },
}

# Evaluation thresholds
MAX_RESPONSE_TIME_SECONDS = 30
MIN_OVERALL_IMPRESSION_LENGTH = 10
MAX_OVERALL_IMPRESSION_LENGTH = 500
MIN_BULLET_POINT_LENGTH = 5

# EXIF-related keywords that should appear when EXIF data is present
EXIF_RELATED_KEYWORDS = [
    "aperture",
    "f-stop",
    "f/",
    "iso",
    "shutter",
    "exposure",
    "focal length",
    "camera",
]
