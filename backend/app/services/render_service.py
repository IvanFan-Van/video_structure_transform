import asyncio
import json
import shutil
import uuid
from pathlib import Path

from sqlmodel import Session

from app.database import engine
from app.models import Asset
from app.repositories import create_asset, get_asset_by_id
from app.schemas.plan import VideoTemplate
from app.services.task import register_and_launch
from app.tasks import task_registry
from app.tasks.model import STREAM_EOF

REMOTION_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "viral-structure-engine"
    / "remotion-video"
)
REMOTION_CLI = str(REMOTION_DIR / "node_modules" / ".bin" / "remotion.cmd")
STORAGE_DIR = Path("storage")
VIDEO_DIR = STORAGE_DIR / "videos"
RENDER_DIR = STORAGE_DIR / "render"
FPS = 30
WIDTH = 1080
HEIGHT = 1920


def start_render_task(user_id: str, plan_id: str) -> str:
    task_id = str(uuid.uuid4())
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    queue: asyncio.Queue = asyncio.Queue(maxsize=64)

    register_and_launch(
        task_id=task_id,
        user_id=user_id,
        task_type="render",
        resource_id=plan_id,
        coro=_run_render(task_id, user_id, plan_id, queue),
        stream_queue=queue,
    )
    return task_id


async def _run_render(
    task_id: str,
    user_id: str,
    plan_id: str,
    queue: asyncio.Queue,
) -> None:
    props_path = None
    bgm_dest = None
    output_asset_id = str(uuid.uuid4())
    output_path = str(VIDEO_DIR / f"{output_asset_id}.mp4")

    try:
        # 1. 读 PlanResult
        _push(queue, {"phase": "loading", "message": "Loading plan data..."})
        plan_task = task_registry.get(plan_id)
        if plan_task is None or plan_task.status != "completed":
            _push(queue, {"phase": "error", "message": "Plan not found or not completed"})
            task_registry.set_error(task_id, "Plan not found or not completed")
            return

        plan = VideoTemplate.model_validate(plan_task.result)

        # 2. 拷贝 BGM
        _push(queue, {"phase": "bgm", "message": "Loading BGM audio..."})
        bgm_filename = None
        bgm_asset_id = plan.bgm_spec.reference_audio_asset_id
        if bgm_asset_id:
            with Session(engine) as session:
                asset = get_asset_by_id(session, bgm_asset_id)
                if asset and Path(asset.path).exists():
                    public_dir = REMOTION_DIR / "public"
                    public_dir.mkdir(parents=True, exist_ok=True)
                    bgm_dest = public_dir / "bgm.wav"
                    shutil.copy2(asset.path, str(bgm_dest))
                    bgm_filename = "bgm.wav"

        # 3. 构建 remotion_props
        _push(queue, {"phase": "building", "message": "Building render config..."})
        props = _build_remotion_props(plan, bgm_filename)
        RENDER_DIR.mkdir(parents=True, exist_ok=True)
        props_path = str(RENDER_DIR / f"{task_id}.json")
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False)

        # 4. 调用 Remotion CLI
        _push(queue, {"phase": "rendering", "progress": 0, "frame": 0, "totalFrames": props["durationInFrames"]})
        await _render_with_progress(props_path, output_path, queue)

        # 5. 创建 Asset
        _push(queue, {"phase": "saving", "message": "Saving output video..."})
        if not Path(output_path).exists():
            task_registry.set_error(task_id, "Remotion 渲染后未找到输出文件")
            return

        import ffmpeg
        probe = ffmpeg.probe(output_path)
        video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        dur = float(probe["format"].get("duration", 0))

        with Session(engine) as session:
            asset = Asset(
                asset_id=output_asset_id,
                user_id=user_id,
                path=str(Path(output_path).resolve()),
                type="video",
            )
            create_asset(session, asset)

        _push_eof(queue)
        task_registry.set_result(
            task_id,
            {
                "asset_id": output_asset_id,
                "path": str(Path(output_path).resolve()),
                "duration": dur,
                "fps": FPS,
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
            },
        )
    except asyncio.CancelledError:
        _push_eof(queue)
        _cleanup(props_path, bgm_dest, output_path)
    except Exception as e:
        _push_eof(queue)
        _cleanup(props_path, bgm_dest, output_path)
        task_registry.set_error(task_id, str(e))


def _build_remotion_props(plan: VideoTemplate, bgm_filename: str | None) -> dict:
    scenes = []
    frame_offset = 0

    for seg in plan.segments:
        duration = seg.end_time - seg.start_time
        if duration <= 0:
            continue
        duration_frames = max(1, int(duration * FPS))

        visual_text = ""
        narration = ""
        fill_method = ""
        for slot in seg.slots:
            if slot.slot_type.value == "visual_text" and slot.value:
                visual_text = slot.value
                fill_method = slot.fill_method.value if slot.fill_method else ""
            elif slot.slot_type.value == "narration" and slot.value:
                narration = slot.value
                fill_method = slot.fill_method.value if slot.fill_method else ""

        text = visual_text or narration or seg.narrative_intent

        scene_type = "text_overlay"
        if fill_method in ("ai_generate", "user_upload", "manual_input"):
            scene_type = "remocn_composed"
        elif not visual_text and not narration:
            scene_type = "text_overlay"

        text_style = _build_text_style(seg)
        beat_frames = _compute_beat_frames(
            plan.bgm_spec.bpm, duration_frames
        )

        scenes.append({
            "id": seg.stage,
            "slot_id": seg.index + 1,
            "startFrame": frame_offset,
            "durationFrames": duration_frames,
            "type": scene_type,
            "text": text,
            "textStyle": text_style,
            "visualHint": seg.narrative_intent,
            "emotion": seg.emotional_tone or "neutral",
            "beatFrames": beat_frames,
            "hasMaterial": bool(visual_text or narration),
            "backgroundVideo": None,
            "backgroundImage": None,
            "backgroundColorFallback": "#0D0D0D",
            "requiredElements": [],
            "gapFilled": True,
            "gapStrategy": "color_bg+text",
            "fill_method": "color_bg",
            "remocnEffects": [],
        })

        frame_offset += duration_frames

    total_frames = frame_offset or 1

    return {
        "fps": FPS,
        "durationInFrames": total_frames,
        "width": WIDTH,
        "height": HEIGHT,
        "scenes": scenes,
        "bgmPath": bgm_filename or "",
        "voiceoverPath": "",
        "voiceoverText": "",
        "ttsRate": "+0%",
        "rhythmPattern": "standard",
        "visualStyle": "mixed",
        "gapReport": [],
        "migrationSummary": {},
    }


def _build_text_style(seg) -> dict:
    pos_y = 50
    animation = "fade_in"
    color = "#FFFFFF"
    font_size = 64

    for slot in seg.slots:
        c = slot.constraints
        if c.position:
            pos_map = {
                "top_center": 15, "center": 50, "bottom_center": 82,
                "overlay_left": 50, "overlay_right": 50, "full_screen": 50,
            }
            pos_y = pos_map.get(c.position.value if hasattr(c.position, "value") else str(c.position), 50)
        if c.appear_style:
            animation = c.appear_style
        if c.emphasis:
            emphasis_map = {
                "zoom": "bounce", "shake": "glitch",
                "color_change": "fade_in", "stroke": "typewriter",
            }
            animation = emphasis_map.get(
                c.emphasis.value if hasattr(c.emphasis, "value") else str(c.emphasis),
                animation,
            )
        if c.max_chars:
            char_count = c.max_chars
            if char_count > 40:
                font_size = 56
            elif char_count > 25:
                font_size = 64
            else:
                font_size = 72

    return {
        "fontSize": font_size,
        "color": color,
        "fontWeight": "bold",
        "animation": animation,
        "position_x": 50,
        "position_y": pos_y,
    }


def _compute_beat_frames(bpm: float | None, duration_frames: int) -> list[int]:
    if not bpm or bpm <= 0:
        return []
    beat_interval_sec = 60.0 / bpm
    beat_interval_frames = beat_interval_sec * FPS
    num_beats = int(duration_frames / beat_interval_frames)
    return [int(i * beat_interval_frames) for i in range(1, num_beats + 1)]


async def _render_with_progress(
    props_path: str,
    output_path: str,
    queue: asyncio.Queue,
) -> None:
    process = await asyncio.create_subprocess_exec(
        REMOTION_CLI, "render",
        "src/index.ts", "VideoComposition", str(output_path),
        f"--props={props_path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(REMOTION_DIR),
    )

    async for line_bytes in process.stdout:  # type: ignore
        line = line_bytes.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        # Parse "Rendering frame 45/498" or percentage output
        if "Rendering frame" in line or "%" in line:
            try:
                parts = line.split()
                for p in parts:
                    if "/" in p and any(c.isdigit() for c in p):
                        frame_str, total_str = p.split("/")
                        frame = int(frame_str)
                        total = int(total_str)
                        progress = int(frame / total * 100)
                        _push(queue, {
                            "phase": "rendering",
                            "progress": progress,
                            "frame": frame,
                            "totalFrames": total,
                        })
                        break
            except (ValueError, IndexError):
                pass

    await process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Remotion render failed with code {process.returncode}")


def _push(queue: asyncio.Queue, data: dict) -> None:
    try:
        queue.put_nowait(data)
    except asyncio.QueueFull:
        pass


def _push_eof(queue: asyncio.Queue) -> None:
    try:
        queue.put_nowait(STREAM_EOF)
    except asyncio.QueueFull:
        pass


def _cleanup(props_path: str | None, bgm_dest: Path | None, output_path: str) -> None:
    if props_path:
        try:
            Path(props_path).unlink(missing_ok=True)
        except OSError:
            pass
    if bgm_dest:
        try:
            bgm_dest.unlink(missing_ok=True)
        except OSError:
            pass
    try:
        Path(output_path).unlink(missing_ok=True)
    except OSError:
        pass
