import asyncio
import json
import logging
import shutil
import uuid
from pathlib import Path

import edge_tts
from sqlmodel import Session

from app.config.config import RENDER_DIR, VIDEO_DIR
from app.config.style_config import get_available_styles, get_style_config
from app.database import engine
from app.models import Asset
from app.repositories import create_asset, get_asset_by_id
from app.schemas.plan import VideoTemplate
from app.services.pipeline import extract_cover_for_video
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
PREVIEW_DIR = STORAGE_DIR / "preview"
FPS = 30
WIDTH = 1080
HEIGHT = 1920

logger = logging.getLogger(__name__)


def start_preview_task(session: Session, user_id: str, plan_id: str) -> str:
    task_id = str(uuid.uuid4())
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    queue: asyncio.Queue = asyncio.Queue(maxsize=64)

    register_and_launch(
        task_id=task_id,
        user_id=user_id,
        task_type="render_preview",
        resource_id=plan_id,
        coro=_run_preview(session, task_id, user_id, plan_id, queue),
        stream_queue=queue,
    )
    return task_id


def start_render_task(
    session: Session, user_id: str, plan_id: str, style: str = "standard"
) -> str:
    task_id = str(uuid.uuid4())
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    queue: asyncio.Queue = asyncio.Queue(maxsize=64)

    register_and_launch(
        task_id=task_id,
        user_id=user_id,
        task_type="render",
        resource_id=plan_id,
        coro=_run_render(session, task_id, user_id, plan_id, style, queue),
        stream_queue=queue,
    )
    return task_id


async def _run_preview(
    session: Session,
    task_id: str,
    user_id: str,
    plan_id: str,
    queue: asyncio.Queue,
) -> None:
    props_path = None
    bgm_dest = None
    preview_dir = PREVIEW_DIR / task_id

    try:
        _push(queue, {"phase": "loading", "message": "Loading plan data..."})
        plan_task = task_registry.get(plan_id)
        if plan_task is None or plan_task.status != "completed":
            _push(
                queue,
                {"phase": "error", "message": "Plan not found or not completed"},
            )
            task_registry.set_error(task_id, "Plan not found or not completed")
            return

        plan = VideoTemplate.model_validate(plan_task.result)

        _push(queue, {"phase": "bgm", "message": "Loading BGM audio..."})
        bgm_filename = None
        bgm_asset_id = plan.bgm_spec.reference_audio_asset_id
        if bgm_asset_id:
            asset = get_asset_by_id(session, bgm_asset_id)
            if asset and Path(asset.path).exists():
                public_dir = REMOTION_DIR / "public"
                public_dir.mkdir(parents=True, exist_ok=True)
                bgm_dest = public_dir / "bgm.wav"
                shutil.copy2(asset.path, str(bgm_dest))
                bgm_filename = "bgm.wav"

        preview_dir.mkdir(parents=True, exist_ok=True)

        styles = get_available_styles()
        results = []
        total = len(styles)

        for i, style_info in enumerate(styles):
            style_name = style_info["name"]
            _push(
                queue,
                {
                    "phase": "building",
                    "message": f"Building {style_name} config ({i + 1}/{total})...",
                    "style": style_name,
                    "styleIndex": i,
                    "totalStyles": total,
                },
            )

            style_config = get_style_config(style_name)
            props = _build_remotion_props(plan, bgm_filename, style_config)

            props_path = str((RENDER_DIR / f"{task_id}_{style_name}.json").resolve())
            with open(props_path, "w", encoding="utf-8") as f:
                json.dump(props, f, ensure_ascii=False)

            midpoint_frame = max(0, props["durationInFrames"] // 3)
            still_path = str((preview_dir / f"{style_name}.png").resolve())

            _push(
                queue,
                {
                    "phase": "rendering",
                    "message": f"Rendering {style_name} preview...",
                    "style": style_name,
                    "styleIndex": i,
                    "totalStyles": total,
                },
            )

            await _render_still(props_path, still_path, midpoint_frame)

            results.append(
                {
                    "style": style_name,
                    "label": style_config.get("label", style_name),
                    "description": style_config.get("description", ""),
                    "still_path": still_path,
                    "duration_frames": props["durationInFrames"],
                    "scene_count": len(props["scenes"]),
                }
            )

        _push_eof(queue)
        task_registry.set_result(task_id, results)
    except asyncio.CancelledError:
        _push_eof(queue)
        _cleanup(props_path, bgm_dest, None)
    except Exception as e:
        logger.exception("Preview task failed")
        _push_eof(queue)
        _cleanup(props_path, bgm_dest, None)
        task_registry.set_error(task_id, str(e))


async def _run_render(
    session: Session,
    task_id: str,
    user_id: str,
    plan_id: str,
    style: str,
    queue: asyncio.Queue,
) -> None:
    props_path = None
    bgm_dest = None
    narration_paths = None
    output_asset_id = str(uuid.uuid4())
    output_path = str((VIDEO_DIR / f"{output_asset_id}.mp4").resolve())

    try:
        _push(queue, {"phase": "loading", "message": "Loading plan data..."})
        plan_task = task_registry.get(plan_id)
        if plan_task is None or plan_task.status != "completed":
            _push(
                queue, {"phase": "error", "message": "Plan not found or not completed"}
            )
            task_registry.set_error(task_id, "Plan not found or not completed")
            return

        plan = VideoTemplate.model_validate(plan_task.result)

        public_dir = REMOTION_DIR / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        _push(queue, {"phase": "bgm", "message": "Loading BGM audio..."})
        bgm_filename = None
        bgm_asset_id = plan.bgm_spec.reference_audio_asset_id
        if bgm_asset_id:
            asset = get_asset_by_id(session, bgm_asset_id)
            if asset and Path(asset.path).exists():
                bgm_dest = public_dir / "bgm.wav"
                shutil.copy2(asset.path, str(bgm_dest))
                bgm_filename = "bgm.wav"

        # 2.5. 生成 narration TTS 音频
        narration_paths = await _generate_all_narration_audio(plan, public_dir, queue)

        # 3. 探测参考视频分辨率
        width = WIDTH
        height = HEIGHT
        if plan.reference_asset_id:
            ref_asset = get_asset_by_id(session, plan.reference_asset_id)
            if ref_asset and Path(ref_asset.path).exists():
                import ffmpeg

                ref_probe = ffmpeg.probe(ref_asset.path)
                ref_vs = next(
                    s for s in ref_probe["streams"] if s["codec_type"] == "video"
                )
                width = ref_vs["width"]
                height = ref_vs["height"]

        # 4. 构建 RemotionProps
        _push(
            queue,
            {
                "phase": "building",
                "message": f"Building render config (style: {style})...",
                "style": style,
            },
        )
        style_config = get_style_config(style)
        props = _build_remotion_props(plan, bgm_filename, style_config, width, height)
        RENDER_DIR.mkdir(parents=True, exist_ok=True)
        props_path = str((RENDER_DIR / f"{task_id}.json").resolve())
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False)

        _push(
            queue,
            {
                "phase": "rendering",
                "progress": 0,
                "frame": 0,
                "totalFrames": props["durationInFrames"],
                "style": style,
            },
        )
        await _render_with_progress(props_path, output_path, queue, style)

        _push(queue, {"phase": "saving", "message": "Saving output video..."})
        if not Path(output_path).exists():
            task_registry.set_error(task_id, "Remotion render output not found")
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

            cover_id = await asyncio.get_running_loop().run_in_executor(
                None,
                extract_cover_for_video,
                session,
                str(Path(output_path).resolve()),
                user_id,
                output_asset_id,
            )

        _push_eof(queue)
        task_registry.set_result(
            task_id,
            {
                "style": style,
                "asset_id": output_asset_id,
                "path": str(Path(output_path).resolve()),
                "duration": dur,
                "fps": FPS,
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "cover_image_asset_id": cover_id,
            },
        )
    except asyncio.CancelledError:
        _push_eof(queue)
        _cleanup(props_path, bgm_dest, output_path, narration_paths)
    except Exception as e:
        logger.exception("Render task failed")
        _push_eof(queue)
        _cleanup(props_path, bgm_dest, output_path, narration_paths)
        task_registry.set_error(task_id, str(e))


async def _generate_narration_audio(
    text: str,
    output_path: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


async def _generate_all_narration_audio(
    plan: VideoTemplate,
    public_dir: Path,
    queue: asyncio.Queue,
) -> list[Path]:
    narration_slots = [
        slot
        for seg in plan.segments
        for slot in seg.slots
        if slot.slot_type.value == "narration" and slot.value
    ]
    if not narration_slots:
        return []

    paths: list[Path] = []
    total = len(narration_slots)
    _push(
        queue,
        {
            "phase": "tts",
            "message": f"Generating narration audio ({total} segments)...",
        },
    )
    for i, slot in enumerate(narration_slots):
        dest = public_dir / f"narration_{slot.slot_id}.wav"
        try:
            await _generate_narration_audio(slot.value, str(dest))
            paths.append(dest)
            _push(
                queue,
                {
                    "phase": "tts",
                    "progress": int((i + 1) / total * 100),
                    "message": f"TTS {i + 1}/{total}: narration_{slot.slot_id}.wav",
                },
            )
        except Exception as e:
            logger.warning("TTS failed for slot %s: %s", slot.slot_id, e)
            _push(
                queue,
                {
                    "phase": "tts",
                    "message": f"TTS failed for narration_{slot.slot_id}: {e}",
                },
            )
    return paths


def _resolve_background_image(seg) -> str | None:
    for slot in seg.slots:
        if slot.slot_type.value == "background_image" and slot.value:
            try:
                with Session(engine) as s:
                    bg_asset = get_asset_by_id(s, slot.value)
                if bg_asset and Path(bg_asset.path).exists():
                    public_dir = REMOTION_DIR / "public"
                    public_dir.mkdir(parents=True, exist_ok=True)
                    dest = public_dir / f"aigc_{seg.index}.png"
                    shutil.copy2(str(bg_asset.path), str(dest))
                    return f"aigc_{seg.index}.png"
            except Exception:
                pass
    return None


def _build_remotion_props(
    plan: VideoTemplate,
    bgm_filename: str | None,
    style_config: dict | None = None,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> dict:
    scenes = []
    frame_offset = 0

    raw_segments = [
        (seg, max(0, seg.end_time - seg.start_time)) for seg in plan.segments
    ]
    raw_total = sum(dur for _, dur in raw_segments)

    total_seconds = plan.estimated_duration
    if raw_total > 0:
        ratio = total_seconds / raw_total
    else:
        ratio = 1.0

    for seg, raw_dur in raw_segments:
        duration = raw_dur * ratio if raw_dur > 0 else 0.01
        duration_frames = max(1, int(duration * FPS))

        visual_text = ""
        narration = ""
        for slot in seg.slots:
            if slot.slot_type.value == "visual_text" and slot.value:
                visual_text = slot.value
            elif slot.slot_type.value == "narration" and slot.value:
                narration = slot.value

        bg_image = _resolve_background_image(seg)

        text = visual_text or narration or seg.narrative_intent

        if seg.stage in ("hook", "story", "insight", "cta") and (
            visual_text or narration
        ):
            scene_type = "emphasis_text"
        else:
            scene_type = "text_overlay"

        text_style = _build_text_style(seg)
        beat_frames = _compute_beat_frames(plan.bgm_spec.bpm, duration_frames)

        scenes.append(
            {
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
                "hasMaterial": bool(visual_text or narration or bg_image),
                "backgroundVideo": None,
                "backgroundImage": bg_image,
                "backgroundColorFallback": "#0D0D0D",
                "requiredElements": [],
                "gapFilled": True,
                "gapStrategy": "aigc_image" if bg_image else "color_bg+text",
                "fill_method": "aigc_image" if bg_image else "color_bg",
                "remocnEffects": [],
            }
        )

        frame_offset += duration_frames

    total_frames = frame_offset or 1

    if style_config:
        _apply_style_mutations(scenes, style_config)
        current = 0
        for s in scenes:
            s["startFrame"] = current
            current += s["durationFrames"]
        total_frames = current or 1

    return {
        "fps": FPS,
        "durationInFrames": total_frames,
        "width": width,
        "height": height,
        "scenes": scenes,
        "bgmPath": bgm_filename or "",
        "voiceoverPath": "",
        "voiceoverText": "",
        "ttsRate": "+0%",
        "rhythmPattern": style_config.get("rhythm_pattern", "standard")
        if style_config
        else "standard",
        "visualStyle": style_config.get("visual_style", "mixed")
        if style_config
        else "mixed",
        "gapReport": [],
        "migrationSummary": {},
    }


def _apply_style_mutations(scenes: list[dict], style_config: dict) -> None:
    duration_scale = style_config.get("duration_scale", 1.0)
    multipliers = style_config.get("stage_duration_multipliers", {}) or {}
    type_overrides = style_config.get("stage_type_overrides", {}) or {}
    min_frames = style_config.get("min_duration_frames", 1)
    text_animation = style_config.get("text_animation")

    for scene in scenes:
        stage = scene.get("id", "")
        mult = multipliers.get(stage, 1.0)
        scene["durationFrames"] = max(
            min_frames, round(scene["durationFrames"] * duration_scale * mult)
        )
        if stage in type_overrides:
            scene["type"] = type_overrides[stage]
        if text_animation:
            scene["textStyle"]["animation"] = text_animation


def _build_text_style(seg) -> dict:
    pos_y = 50
    animation = "fade_in"
    color = "#FFFFFF"
    font_size = 64

    for slot in seg.slots:
        c = slot.constraints
        if c.position:
            pos_map = {
                "top_center": 15,
                "center": 50,
                "bottom_center": 82,
                "overlay_left": 50,
                "overlay_right": 50,
                "full_screen": 50,
            }
            pos_y = pos_map.get(
                c.position.value if hasattr(c.position, "value") else str(c.position),
                50,
            )
        if c.appear_style:
            animation = c.appear_style
        if c.emphasis:
            emphasis_map = {
                "zoom": "bounce",
                "shake": "glitch",
                "color_change": "fade_in",
                "stroke": "typewriter",
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


async def _render_still(props_path: str, output_path: str, frame: int = 0) -> None:
    process = await asyncio.create_subprocess_exec(
        REMOTION_CLI,
        "still",
        "src/index.ts",
        f"--props={props_path}",
        f"--frame={frame}",
        f"--output={output_path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(REMOTION_DIR),
    )

    stdout_lines: list[str] = []
    async for line_bytes in process.stdout:  # type: ignore
        line = line_bytes.decode("utf-8", errors="replace").strip()
        if line:
            stdout_lines.append(line)

    await process.wait()

    if process.returncode != 0:
        tail = "\n".join(stdout_lines[-30:]) if stdout_lines else "(no output)"
        raise RuntimeError(
            f"Remotion still failed with code {process.returncode}\n{tail}"
        )


async def _render_with_progress(
    props_path: str,
    output_path: str,
    queue: asyncio.Queue,
    style: str = "standard",
) -> None:
    process = await asyncio.create_subprocess_exec(
        REMOTION_CLI,
        "render",
        "src/index.ts",
        "VideoComposition",
        str(output_path),
        f"--props={props_path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(REMOTION_DIR),
    )

    lines: list[str] = []

    async for line_bytes in process.stdout:  # type: ignore
        line = line_bytes.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        lines.append(line)
        if "Rendering frame" in line or "%" in line:
            try:
                parts = line.split()
                for p in parts:
                    if "/" in p and any(c.isdigit() for c in p):
                        frame_str, total_str = p.split("/")
                        frame = int(frame_str)
                        total = int(total_str)
                        progress = int(frame / total * 100)
                        _push(
                            queue,
                            {
                                "phase": "rendering",
                                "progress": progress,
                                "frame": frame,
                                "totalFrames": total,
                                "style": style,
                            },
                        )
                        break
            except (ValueError, IndexError):
                pass

    await process.wait()

    if process.returncode != 0:
        tail = "\n".join(lines[-30:]) if lines else "(no output)"
        raise RuntimeError(
            f"Remotion render failed with code {process.returncode}\n{tail}"
        )


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


def _cleanup(
    props_path: str | None,
    bgm_dest: Path | None,
    output_path: str | None,
    narration_paths: list[Path] | None = None,
) -> None:
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
    if narration_paths:
        for p in narration_paths:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
    if output_path:
        try:
            Path(output_path).unlink(missing_ok=True)
        except OSError:
            pass
