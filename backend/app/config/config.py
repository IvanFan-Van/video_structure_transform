from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
print(f"Repository root: {REPO_ROOT}")

BACKEND_ROOT = REPO_ROOT / "backend"
STORAGE_DIR = BACKEND_ROOT / "storage"
EFFECT_DIR = STORAGE_DIR / "effects"
EFFECT_DOC_DIR = STORAGE_DIR / "effect_docs"
VIDEO_DIR = STORAGE_DIR / "videos"
AUDIO_DIR = STORAGE_DIR / "audios"
IMAGE_DIR = STORAGE_DIR / "images"
RENDER_DIR = STORAGE_DIR / "render"
TMP_DIR = STORAGE_DIR / "tmp"

MODELS_DIR = BACKEND_ROOT / "models"

COMPONENTS_JSON = BACKEND_ROOT / "components_description.json"

REMOTION_DIR = REPO_ROOT / "effects-renderer"
