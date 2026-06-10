import asyncio
import json
import os
import uuid
from datetime import UTC, datetime

import instructor
from pydantic import ValidationError
from sqlmodel import Session as SqlSession

from app.database import engine as db_engine
from app.llm import async_client
from app.models import Asset
from app.prompts import (
    PLAN_SYSTEM_PROMPT,
    PLAN_USER_PROMPT_HEADER,
    PLAN_USER_PROMPT_SCRIPT_SECTION,
    PLAN_USER_PROMPT_TASK,
    PLAN_USER_PROMPT_VISUAL_SECTION,
    SLOT_GENERATION_SYSTEM_PROMPT,
    SLOT_GENERATION_USER_TEMPLATE,
)
from app.repositories import create_asset as crt_asset
from app.schemas.plan import (
    BgmSpec,
    FillMethod,
    PlanOutput,
    PlanRequest,
    Segment,
    Slot,
    SlotConstraints,
    SlotGenerationOutput,
    SlotStatus,
    SlotType,
    TransitionSpec,
    VideoTemplate,
)
from app.schemas.visual import CameraMovement
from app.services.image_service import generate_image
from app.services.task import register_and_launch
from app.tasks import task_registry


def _build_user_prompt(
    script_result: dict | None,
    visual_result: dict | None,
    user_brief: str,
    estimated_duration: float,
    narrator_perspective: str | None,
) -> str:
    parts = [PLAN_USER_PROMPT_HEADER]

    if script_result:
        parts.append(
            PLAN_USER_PROMPT_SCRIPT_SECTION.format(
                script_json=json.dumps(script_result, ensure_ascii=False, indent=2),
            )
        )

    if visual_result:
        parts.append(
            PLAN_USER_PROMPT_VISUAL_SECTION.format(
                total_duration=visual_result["total_duration"],
                avg_shot_duration=visual_result["pacing"]["avg_shot_duration"],
                pacing_category=visual_result["pacing"]["pacing_category"],
                shots_json=json.dumps(
                    visual_result["shots"], ensure_ascii=False, indent=2
                ),
            )
        )

    parts.append(
        PLAN_USER_PROMPT_TASK.format(
            user_brief=user_brief,
            estimated_duration=estimated_duration,
            narrator_perspective=narrator_perspective or "参考原视频或自行判断",
        )
    )

    return "\n".join(parts)


def _find_transition(
    end_time: float, transition_map: dict[float, TransitionSpec]
) -> TransitionSpec:
    key = round(end_time, 2)
    for k, v in transition_map.items():
        if abs(k - key) <= 0.5:
            return v
    return TransitionSpec(type="cut", duration=0.0)


def _find_camera_movement(
    seg_start: float,
    seg_end: float,
    scaled_shots: list[dict],
) -> CameraMovement | None:
    best_shot = None
    best_overlap = 0.0
    for shot in scaled_shots:
        overlap_start = max(seg_start, shot["start_time_scaled"])
        overlap_end = min(seg_end, shot["end_time_scaled"])
        overlap = max(0.0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_shot = shot
    if best_shot and best_shot.get("camera_movement"):
        return best_shot["camera_movement"]
    return None


def _gather_analysis_results(request: PlanRequest) -> tuple:
    """Fetch analysis results from task_registry. Returns 4-tuple of optional dicts."""
    script_result = None
    visual_result = None
    audio_result = None
    effect_result = None

    if request.script_task_id:
        script_task = task_registry.get(request.script_task_id)
        if script_task:
            script_result = script_task.result
    if request.visual_task_id:
        visual_task = task_registry.get(request.visual_task_id)
        if visual_task:
            visual_result = visual_task.result
    if request.audio_task_id:
        audio_task = task_registry.get(request.audio_task_id)
        if audio_task:
            audio_result = audio_task.result
    if request.effect_task_id:
        effect_task = task_registry.get(request.effect_task_id)
        if effect_task:
            effect_result = effect_task.result

    return script_result, visual_result, audio_result, effect_result


def _build_coordinate_maps(
    visual_result: dict | None,
    estimated_duration: float,
) -> tuple[list[dict], dict[float, TransitionSpec]]:
    """Build time-scaled shot list and transition map for matching."""
    if not visual_result or not visual_result.get("total_duration"):
        return [], {}

    original_duration = float(visual_result["total_duration"])
    scale = estimated_duration / original_duration if original_duration > 0 else 1.0

    scaled_shots: list[dict] = []
    shot_end_map: dict[int, float] = {}
    for shot in visual_result.get("shots", []):
        s = dict(shot)
        s["start_time_scaled"] = shot["start_time"] * scale
        s["end_time_scaled"] = shot["end_time"] * scale
        scaled_shots.append(s)
        shot_end_map[shot["shot_index"]] = round(shot["end_time"] * scale, 2)

    transition_map: dict[float, TransitionSpec] = {}
    for t in visual_result.get("transitions", []):
        scaled_end = shot_end_map.get(t["after_shot_index"])
        if scaled_end is not None:
            transition_map[scaled_end] = TransitionSpec(
                type=t["type"], duration=t["duration"]
            )

    return scaled_shots, transition_map


def _get_reference_asset_id(request: PlanRequest) -> str | None:
    """Determine the reference video asset_id from related tasks."""
    if request.visual_task_id:
        visual_task = task_registry.get(request.visual_task_id)
        if visual_task:
            return visual_task.resource_id
    if request.script_task_id:
        script_task = task_registry.get(request.script_task_id)
        if script_task:
            return script_task.resource_id
    return None


def _preprocess_plan_input(request: PlanRequest) -> dict:
    """Gather analysis results from task_registry and compute preprocessed data."""
    script_result, visual_result, audio_result, effect_result = (
        _gather_analysis_results(request)
    )

    # estimated_duration
    if request.target_duration:
        estimated_duration = request.target_duration
    elif visual_result and visual_result.get("total_duration"):
        estimated_duration = float(visual_result["total_duration"])
    elif script_result:
        stage_end_times = []
        stages = script_result.get("stages", {})
        for s in stages.values():
            if s is not None and s.get("end_time"):
                stage_end_times.append(float(s["end_time"]))
        estimated_duration = max(stage_end_times) if stage_end_times else 60.0
    else:
        estimated_duration = 60.0

    # narrator_perspective
    narrator_perspective = None
    if script_result:
        narrator_perspective = script_result.get("narrator_perspective")

    # bgm_spec
    bgm_slot = Slot(
        slot_id="bgm_main",
        slot_type=SlotType.bgm,
        description="背景音乐素材",
        constraints=SlotConstraints(),
    )
    bgm_spec = BgmSpec(
        genre=audio_result.get("genre") if audio_result else None,
        bpm=audio_result.get("estimated_bpm") if audio_result else None,
        mood=None,
        reference_audio_asset_id=(
            audio_result.get("audio_asset_id") if audio_result else None
        ),
        slot=bgm_slot,
    )

    # effects
    all_effects: list[str] = []
    if effect_result:
        all_effects = [e["name"] for e in effect_result.get("effects", [])]

    # time coordinate maps
    scaled_shots, transition_map = _build_coordinate_maps(
        visual_result, estimated_duration
    )

    return {
        "script_result": script_result,
        "visual_result": visual_result,
        "estimated_duration": estimated_duration,
        "narrator_perspective": narrator_perspective,
        "bgm_spec": bgm_spec,
        "reference_asset_id": _get_reference_asset_id(request),
        "all_effects": all_effects,
        "scaled_shots": scaled_shots,
        "transition_map": transition_map,
    }


def _build_segments_from_llm_output(
    plan_output: PlanOutput,
    all_effects: list[str],
    scaled_shots: list[dict],
    transition_map: dict[float, TransitionSpec],
) -> list[Segment]:
    """Build Segment objects from LLM output, merging with visual analysis data."""
    segments: list[Segment] = []
    for raw_seg in plan_output.segments:
        slots: list[Slot] = []
        for raw_slot in raw_seg.slots:
            constraints = raw_slot.constraints
            try:
                slot_constraints = SlotConstraints(
                    **constraints.model_dump() if constraints else {}
                )
            except ValidationError:
                slot_constraints = SlotConstraints()
            slots.append(
                Slot(
                    slot_id=f"seg{raw_seg.index}_{raw_slot.slot_type}",
                    slot_type=SlotType(raw_slot.slot_type),
                    description=raw_slot.description,
                    constraints=slot_constraints,
                    status=SlotStatus.empty,
                )
            )

        seg = Segment(
            index=raw_seg.index,
            stage=raw_seg.stage,
            start_time=raw_seg.start_time,
            end_time=raw_seg.end_time,
            narrative_intent=raw_seg.narrative_intent,
            hook_type=raw_seg.hook_type,
            cta_type=raw_seg.cta_type,
            emotional_tone=raw_seg.emotional_tone,
            is_text_frame=raw_seg.is_text_frame,
            camera_movement=_find_camera_movement(
                raw_seg.start_time, raw_seg.end_time, scaled_shots
            ),
            effects=(all_effects if raw_seg.stage in ("hook", "cta") else []),
            transition_out=_find_transition(raw_seg.end_time, transition_map),
            slots=slots,
        )
        segments.append(seg)
    return segments


async def run_plan_generation(task_id: str, request: PlanRequest, user_id: str) -> None:
    try:
        # ── Steps 1 & 2: gather and preprocess ───────────────
        pre = _preprocess_plan_input(request)

        # ── Step 3: call LLM ─────────────────────────────────
        user_prompt = _build_user_prompt(
            script_result=pre["script_result"],
            visual_result=pre["visual_result"],
            user_brief=request.user_brief,
            estimated_duration=pre["estimated_duration"],
            narrator_perspective=pre["narrator_perspective"],
        )

        instructor_client = instructor.from_openai(async_client)
        plan_output: PlanOutput = await instructor_client.chat.completions.create(
            model=os.getenv("MODEL"),  # type: ignore
            response_model=PlanOutput,
            messages=[
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        # ── Step 4: build segments from LLM output ────────────
        segments = _build_segments_from_llm_output(
            plan_output=plan_output,
            all_effects=pre["all_effects"],
            scaled_shots=pre["scaled_shots"],
            transition_map=pre["transition_map"],
        )

        # ── Step 5: build and store VideoTemplate ─────────────
        pre["bgm_spec"].mood = plan_output.bgm_mood

        template = VideoTemplate(
            plan_id=task_id,
            created_at=datetime.now(UTC).isoformat(),
            user_id=user_id,
            user_brief=request.user_brief,
            reference_asset_id=pre["reference_asset_id"],
            estimated_duration=pre["estimated_duration"],
            narrator_perspective=pre["narrator_perspective"],
            bgm_spec=pre["bgm_spec"],
            segments=segments,
        )
        task_registry.set_result(task_id, template.model_dump())

    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


def start_plan_generation(request: PlanRequest, user_id: str) -> str:
    task_id = str(uuid.uuid4())
    resource_id = _get_reference_asset_id(request) or ""

    register_and_launch(
        task_id=task_id,
        user_id=user_id,
        task_type="plan",
        resource_id=resource_id,
        coro=run_plan_generation(task_id, request, user_id),
    )
    return task_id


def _build_slot_gen_prompt(template: VideoTemplate) -> str:
    segments_lines: list[str] = []
    type_hints = {
        "visual_text": lambda c: f"最大{c.max_chars}字"
        if c and c.max_chars
        else "画面文字",
        "narration": lambda c: f"最大{c.max_duration_sec}秒"
        if c and c.max_duration_sec
        else "旁白",
        "background_video": lambda c: "背景视频",
        "background_image": lambda c: "背景图片",
    }

    for seg in template.segments:
        seg_lines = [
            f"\nseg{seg.index} ({seg.stage}, {seg.start_time}-{seg.end_time}s): "
            f'intent="{seg.narrative_intent}"'
        ]
        for slot in seg.slots:
            hint_fn = type_hints.get(
                slot.slot_type.value, lambda c: slot.slot_type.value
            )
            hint = hint_fn(slot.constraints)
            if slot.status == SlotStatus.filled:
                tag = f'[已填] "{slot.value}"'
            elif slot.status == SlotStatus.pending:
                tag = "[待生成]"
            else:
                tag = "[未填]"
            seg_lines.append(f"  {slot.slot_type.value}: {hint} {tag}")
        segments_lines.append("\n".join(seg_lines))

    return SLOT_GENERATION_USER_TEMPLATE.format(
        user_brief=template.user_brief,
        template_segments="\n".join(segments_lines),
    )


async def _generate_background_images(
    pending_image: list[tuple[Segment, Slot]],
    template: VideoTemplate,
    user_id: str,
) -> tuple[int, list[str]]:
    generated = 0
    warnings: list[str] = []
    for seg, slot in pending_image:
        prompt_parts = [slot.description, template.user_brief]
        if seg.narrative_intent:
            prompt_parts.append(seg.narrative_intent)
        prompt = "，".join(p for p in prompt_parts if p.strip())

        image_path, err = await generate_image(prompt)
        if image_path:
            asset_id = str(uuid.uuid4())
            with SqlSession(db_engine) as s:
                asset = Asset(
                    asset_id=asset_id,
                    user_id=user_id,
                    path=image_path,
                    type="image",
                )
                crt_asset(s, asset)

            slot.value = asset_id
            slot.status = SlotStatus.filled
            slot.fill_method = FillMethod.ai_generate
            generated += 1
        elif err:
            warnings.append(f"{slot.slot_id}: {err}")
    return generated, warnings


async def run_slot_generation(  # noqa: C901
    task_id: str, plan_id: str, user_id: str
) -> None:
    try:
        plan_task = task_registry.get(plan_id)
        if plan_task is None or plan_task.type != "plan":
            task_registry.set_error(task_id, "计划不存在")
            return

        template = VideoTemplate.model_validate(plan_task.result)

        pending_text: list[tuple[Segment, Slot]] = []
        pending_image: list[tuple[Segment, Slot]] = []
        for seg in template.segments:
            for slot in seg.slots:
                if slot.status == SlotStatus.pending:
                    if slot.slot_type in (SlotType.visual_text, SlotType.narration):
                        pending_text.append((seg, slot))
                    elif slot.slot_type == SlotType.background_image:
                        pending_image.append((seg, slot))

        generated_count = 0
        img_warnings: list[str] = []
        output = None  # type: ignore

        if not pending_text and not pending_image:
            task_registry.set_result(
                task_id, {"generated_slots": [], "message": "没有待生成的槽位"}
            )

        if pending_text:
            user_prompt = _build_slot_gen_prompt(template)

            instructor_client = instructor.from_openai(async_client)
            output: SlotGenerationOutput = (
                await instructor_client.chat.completions.create(
                    model=os.getenv("MODEL"),  # type: ignore
                    response_model=SlotGenerationOutput,
                    messages=[
                        {"role": "system", "content": SLOT_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
            )

            gen_map = {s.slot_id: s.value for s in output.generated_slots}
            for seg, slot in pending_text:
                val = gen_map.get(slot.slot_id)
                if val:
                    slot.value = val
                    slot.status = SlotStatus.filled
                    slot.fill_method = FillMethod.ai_generate
                    generated_count += 1

        if pending_image:
            img_count, img_warnings = await _generate_background_images(
                pending_image, template, user_id
            )
            generated_count += img_count

        plan_task.result = template.model_dump()
        result: dict = {"generated": generated_count}
        if img_warnings:
            result["warnings"] = img_warnings

        plan_task.result = template.model_dump()
        if output is not None:
            result["generated_slots"] = [
                {"slot_id": s.slot_id, "value": s.value} for s in output.generated_slots
            ]
        task_registry.set_result(task_id, result)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


def start_slot_generation(plan_id: str, user_id: str) -> str:
    task_id = str(uuid.uuid4())
    register_and_launch(
        task_id=task_id,
        user_id=user_id,
        task_type="slot-generation",
        resource_id=plan_id,
        coro=run_slot_generation(task_id, plan_id, user_id),
    )
    return task_id
