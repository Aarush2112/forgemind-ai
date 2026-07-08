from pathlib import Path

# ---------------------------------------------------------
# Base Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODELS_DIR = BASE_DIR / "models"
WEIGHTS_DIR = BASE_DIR / "weights"
OUTPUT_DIR = BASE_DIR / "outputs"
RESULTS_DIR = BASE_DIR / "results"
MODEL_PATH = WEIGHTS_DIR / "best.pt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Image Settings
# ---------------------------------------------------------

SUPPORTED_IMAGE_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp"
]

MAX_IMAGE_SIZE = 4096

# ---------------------------------------------------------
# OpenCV Settings
# ---------------------------------------------------------

GAUSSIAN_KERNEL = (5, 5)

ADAPTIVE_THRESHOLD_BLOCKSIZE = 31

ADAPTIVE_THRESHOLD_C = 15

# ---------------------------------------------------------
# YOLO Settings
# ---------------------------------------------------------

YOLO_CONFIDENCE = 0.30

YOLO_IOU = 0.45

YOLO_IMAGE_SIZE = 1280

# ---------------------------------------------------------
# OCR Settings
# ---------------------------------------------------------

OCR_LANG = "en"

# ---------------------------------------------------------
# Thresholding Settings
# ---------------------------------------------------------

THRESHOLD_METHOD = "otsu"  # or "adaptive"
THRESHOLD_BLOCK_SIZE = 31
THRESHOLD_C = 10

# ---------------------------------------------------------
# Morphological Operations Settings
# ---------------------------------------------------------

MORPHOLOGICAL_OPERATIONS = ["opening", "closing"]  # List of operations to apply
MORPHOLOGICAL_KERNEL_SIZE = (3, 3)

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

LOG_LEVEL = "INFO"