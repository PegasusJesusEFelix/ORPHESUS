import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

QWEN_MODEL = "Qwen/Qwen3-VL-8B-Instruct"
YUE_STAGE1 = "m-a-p/YuE-s1-7B-anneal-en-cot"
YUE_STAGE2 = "m-a-p/YuE-s2-1B-general"

QWEN_GPU = int(os.getenv("ORPHEUS_QWEN_GPU", "0"))
YUE_GPU = int(os.getenv("ORPHEUS_YUE_GPU", "1"))

# Runtime performance / memory toggles (0 or 1)
# Set ORPHEUS_PRELOAD_MODELS=0 to delay heavy model loads until first use.
ORPHEUS_PRELOAD_MODELS = int(os.getenv("ORPHEUS_PRELOAD_MODELS", "1"))
# Keep Qwen resident on GPU after generation (useful for low-latency repeated calls).
# Default 0 to free VRAM after a generation to maximize memory available to other processes.
ORPHEUS_KEEP_QWEN_IN_MEMORY = int(os.getenv("ORPHEUS_KEEP_QWEN_IN_MEMORY", "0"))

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"
YUE_DIR = BASE_DIR / "YuE"

for path in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    path.mkdir(parents=True, exist_ok=True)

SUPPORTED_UPLOAD_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

QWEN_MAX_TOKENS = 1400
QWEN_TEMPERATURE = 0.7
QWEN_TOP_P = 0.8
QWEN_TOP_K = 20

YUE_MAX_NEW_TOKENS = 3000
YUE_REPETITION_PENALTY = 1.1
YUE_RUN_SEGMENTS = 2
YUE_STAGE2_BATCH_SIZE = 1

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_STUDY_TEXT_CHARS = 24_000
