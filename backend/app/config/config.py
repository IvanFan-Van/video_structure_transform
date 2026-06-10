from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()

STORAGE_DIR = REPO_ROOT / "storage"
EFFECT_DIR = STORAGE_DIR / "effects"
VIDEO_DIR = STORAGE_DIR / "videos"
AUDIO_DIR = STORAGE_DIR / "audios"
IMAGE_DIR = STORAGE_DIR / "images"
RENDER_DIR = STORAGE_DIR / "render"
TMP_DIR = STORAGE_DIR / "tmp"

MODELS_DIR = REPO_ROOT / "models"

COMPONENTS_JSON = REPO_ROOT / "components_description.json"
