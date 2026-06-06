"""Split all videos in tests/videos/ using PySceneDetect.

Results are placed in tests/output/<video_name>/.
"""

import shutil
from pathlib import Path

from scenedetect import ContentDetector, detect, split_video_ffmpeg

VIDEOS_DIR = Path(__file__).parent / "videos"
OUTPUT_DIR = Path(__file__).parent / "output"
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}


def split_scenes(video_path: Path) -> None:
    print(f"\n{'=' * 60}")
    print(f"Processing: {video_path.name}")

    out_dir = OUTPUT_DIR / video_path.stem
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    print(f"  Detecting scenes...")
    scene_list = detect(str(video_path), ContentDetector())

    if not scene_list:
        print(f"  No scene changes detected, copying whole video as one scene.")
        shutil.copy2(str(video_path), str(out_dir / video_path.name))
        return

    print(f"  Found {len(scene_list)} scene(s), splitting...")
    split_video_ffmpeg(
        str(video_path),
        scene_list,
        output_dir=str(out_dir),
        show_progress=True,
    )
    print(f"  Done → {out_dir}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    videos = sorted(
        p
        for p in VIDEOS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not videos:
        print(f"No video files found in {VIDEOS_DIR}")
        return

    print(f"Found {len(videos)} video(s) in {VIDEOS_DIR}")

    for video in videos:
        split_scenes(video)

    print(f"\nAll done. Results in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
