"""
cv2 video measurement engine — 逐帧精确测量动画参数

    seed-lite 说"这段是 typewriter + highlight"
    → 这个引擎测出精确的帧号/速度/位移值
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


# ═══════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════

def _roi_from_position(
    frame_w: int, frame_h: int,
    x_pct: float, y_pct: float,
    size_ratio: float = 0.5,
) -> tuple[int, int, int, int]:
    """根据百分比坐标计算文字区域像素矩形 (x1, y1, x2, y2)。"""
    cx = int(frame_w * x_pct / 100)
    cy = int(frame_h * y_pct / 100)
    half_w = int(frame_w * size_ratio / 2)
    half_h = int(frame_h * size_ratio / 4)
    x1 = max(0, cx - half_w)
    y1 = max(0, cy - half_h)
    x2 = min(frame_w, cx + half_w)
    y2 = min(frame_h, cy + half_h)
    return x1, y1, x2, y2


def _roi_mean_brightness(frame: np.ndarray, roi: tuple[int, int, int, int]) -> float:
    """计算 ROI 区域的平均灰度值。"""
    x1, y1, x2, y2 = roi
    if x2 <= x1 or y2 <= y1:
        return 0.0
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    patch = gray[y1:y2, x1:x2]
    return float(np.mean(patch))


# ═══════════════════════════════════════════════════════════════════════
# 核心测量函数
# ═══════════════════════════════════════════════════════════════════════

def measure_visibility(
    video_path: str, roi_bbox: tuple[int, int, int, int],
    start_frame: int, end_frame: int,
) -> list[dict]:
    """
    逐帧测量 ROI 区域的可见性（0=不可见, 1=最亮）。
    返回 [{frame, value}, ...] 列表。
    """
    cap = cv2.VideoCapture(video_path)
    samples: list[dict] = []
    bg_brightness: float | None = None

    for f in range(start_frame, end_frame + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ret, frame = cap.read()
        if not ret:
            continue
        brightness = _roi_mean_brightness(frame, roi_bbox)
        # 用第一帧作为背景基准
        if bg_brightness is None:
            bg_brightness = brightness
        # 归一化到 0~1
        opacity = max(0.0, min(1.0, (brightness - bg_brightness) / max(abs(bg_brightness - 255), 1.0)))
        samples.append({"frame": f, "value": round(opacity, 3)})

    cap.release()
    return samples


def measure_displacement(
    video_path: str, roi_bbox: tuple[int, int, int, int],
    start_frame: int, end_frame: int,
) -> list[dict]:
    """
    光流法追踪 ROI 内文字在 X 轴的平均位移。
    返回 [{frame, dx, dy}, ...]。
    """
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    ret, prev = cap.read()
    if not ret:
        cap.release()
        return []

    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    x1, y1, x2, y2 = roi_bbox
    prev_roi = prev_gray[y1:y2, x1:x2]

    samples: list[dict] = [{"frame": start_frame, "dx": 0.0, "dy": 0.0}]

    for f in range(start_frame + 1, end_frame + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ret, frame = cap.read()
        if not ret:
            continue
        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        curr_roi = curr_gray[y1:y2, x1:x2]

        # 光流
        flow = cv2.calcOpticalFlowFarneback(
            prev_roi, curr_roi, None, 0.5, 3, 15, 3, 5, 1.2, 0,
        )
        dx = float(np.mean(flow[:, :, 0]))
        dy = float(np.mean(flow[:, :, 1]))
        # 累积位移
        prev_dx = samples[-1]["dx"]
        prev_dy = samples[-1]["dy"]
        samples.append({"frame": f, "dx": round(prev_dx + dx, 2), "dy": round(prev_dy + dy, 2)})
        prev_roi = curr_roi

    cap.release()
    return samples


def measure_scale(
    video_path: str, roi_bbox: tuple[int, int, int, int],
    start_frame: int, end_frame: int,
) -> list[dict]:
    """
    检测 ROI 内 blob 的 bounding box 尺寸变化，推算缩放比例。
    返回 [{frame, scale}, ...]。
    """
    cap = cv2.VideoCapture(video_path)
    samples: list[dict] = []
    init_area: float | None = None

    for f in range(start_frame, end_frame + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ret, frame = cap.read()
        if not ret:
            continue
        x1, y1, x2, y2 = roi_bbox
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        roi = gray[y1:y2, x1:x2]
        # 二值化提取文字 blob
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
            area = w * h
        else:
            area = 1.0

        if init_area is None:
            init_area = max(area, 1.0)

        scale = np.sqrt(area / init_area) if area > 0 and init_area > 0 else 0.0
        samples.append({"frame": f, "scale": round(min(scale, 3.0), 3)})

    cap.release()
    return samples


def measure_typewriter_speed(
    video_path: str, roi_bbox: tuple[int, int, int, int],
    start_frame: int, end_frame: int, fps: float, slow_factor: int = 4,
) -> float:
    """
    用 easyocr 每隔 slow_factor 帧识别一次可见字符数，线性拟合 chars/sec。
    返回 chars_per_second 浮点值。
    """
    try:
        import easyocr
    except ImportError:
        return 10.0  # fallback

    reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    cap = cv2.VideoCapture(video_path)
    char_counts: list[tuple[int, int]] = []

    for f in range(start_frame, end_frame + 1, slow_factor):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ret, frame = cap.read()
        if not ret:
            continue
        x1, y1, x2, y2 = roi_bbox
        roi = frame[y1:y2, x1:x2]
        results = reader.readtext(roi, detail=0)
        text = "".join(results).strip()
        char_counts.append((f, len(text)))

    cap.release()

    if len(char_counts) < 3:
        return 10.0

    # 线性拟合: 帧号 → 字符数
    frames_arr = np.array([c[0] - start_frame for c in char_counts], dtype=np.float64)
    chars_arr = np.array([c[1] for c in char_counts], dtype=np.float64)
    slope, _ = np.polyfit(frames_arr, chars_arr, 1)
    chars_per_sec = max(2.0, float(slope * fps))
    return round(chars_per_sec, 1)


# ═══════════════════════════════════════════════════════════════════════
# 曲线 → animation_phases 转换
# ═══════════════════════════════════════════════════════════════════════

EASING_LIST = [
    "Easing.linear",
    "Easing.ease",
    "Easing.out(Easing.quad)",
    "Easing.out(Easing.cubic)",
    "Easing.out(Easing.exp)",
    "Easing.out(Easing.back(1.5))",
    "Easing.in(Easing.exp)",
    "Easing.inOut(Easing.quad)",
]


def _detect_phases_from_curve(
    values: list[float], threshold: float = 0.03,
) -> list[dict]:
    """
    从连续测量值中检测阶段:
    - 值持续上升 → enter
    - 值持续下降 → exit
    - 值平稳 → hold
    返回 [{phase, start_idx, end_idx, from_value, to_value}, ...]
    """
    n = len(values)
    if n < 2:
        return []

    # 计算一阶差分
    diff = [values[i + 1] - values[i] for i in range(n - 1)]

    phases: list[dict] = []
    i = 0
    while i < len(diff):
        # 跳过噪声
        if abs(diff[i]) < threshold:
            i += 1
            continue

        start = i
        upward = diff[i] > 0
        while i < len(diff):
            current_dir = diff[i] > 0 if abs(diff[i]) >= threshold else upward
            if current_dir != upward and abs(diff[i]) >= threshold * 2:
                break
            i += 1
        end = min(i, len(diff))

        if upward:
            phases.append({
                "phase": "enter",
                "start_idx": start,
                "end_idx": end + 1,
                "from_value": round(values[start], 3),
                "to_value": round(values[min(end + 1, n - 1)], 3),
            })
        else:
            phases.append({
                "phase": "exit",
                "start_idx": start,
                "end_idx": end + 1,
                "from_value": round(values[start], 3),
                "to_value": round(values[min(end + 1, n - 1)], 3),
            })

    # 填充 hold phases
    if phases:
        sorted_phases = sorted(phases, key=lambda p: p["start_idx"])
        merged: list[dict] = []
        last_end = 0
        for ph in sorted_phases:
            if ph["start_idx"] > last_end + 1:
                merged.append({
                    "phase": "hold",
                    "start_idx": last_end,
                    "end_idx": ph["start_idx"],
                    "from_value": round(values[last_end], 3),
                    "to_value": round(values[ph["start_idx"]], 3),
                })
            merged.append(ph)
            last_end = ph["end_idx"]
        # 末尾 hold
        if last_end < n - 1:
            merged.append({
                "phase": "hold",
                "start_idx": last_end,
                "end_idx": n - 1,
                "from_value": round(values[last_end], 3),
                "to_value": round(values[n - 1], 3),
            })
        return merged

    return [{
        "phase": "hold",
        "start_idx": 0,
        "end_idx": n - 1,
        "from_value": round(values[0], 3),
        "to_value": round(values[-1], 3),
    }]


def _sample_to_easing(values: list[float], is_enter: bool) -> str:
    """
    根据采样值的变化率模式猜缓动类型。
    """
    n = len(values)
    if n < 3:
        return "Easing.linear"

    # 计算速度变化（加速度）
    speeds = [values[i + 1] - values[i] for i in range(n - 1)]
    avg_speed = sum(abs(v) for v in speeds) / max(len(speeds), 1)

    if avg_speed < 0.01:
        return "Easing.linear"

    # 检测加速/减速模式
    first_half = sum(abs(v) for v in speeds[: len(speeds) // 2])
    second_half = sum(abs(v) for v in speeds[len(speeds) // 2 :])
    ratio = first_half / max(second_half, 0.001)

    if is_enter:
        if ratio > 2:
            return "Easing.out(Easing.cubic)"
        if ratio < 0.5:
            return "Easing.in(Easing.exp)"
        return "Easing.out(Easing.exp)"
    else:
        if ratio > 2:
            return "Easing.in(Easing.exp)"
        if ratio < 0.5:
            return "Easing.out(Easing.exp)"
        return "Easing.in(Easing.exp)"


# ═══════════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════════

def measure_scene_animation(
    video_path: str | Path,
    scene: dict,
    fps: float,
) -> dict:
    """
    对一个场景的所有 element 做 cv2 逐帧测量，返回 animation_phases。

    scene 格式: {
        "start_frame": 0, "end_frame": 50,
        "elements": [{ "element_id": "main_text", "effect": "typewriter",
                       "position": {"x_percent": 50, "y_percent": 50}, ... }]
    }

    返回值: { "elements": [{ "element_id": ..., "animation_phases": [...], "effect_params": {...} }] }
    """
    vpath = str(video_path)
    sf = scene["start_frame"]
    ef = scene["end_frame"]
    elements = scene.get("elements", [])

    result_elements: list[dict] = []

    cap = cv2.VideoCapture(vpath)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    cap.release()

    for elem in elements:
        eid = elem.get("element_id", "unknown")
        eff = elem.get("effect", "static")
        pos = elem.get("position", {"x_percent": 50, "y_percent": 50})
        ep = elem.get("effect_params", {})
        px = pos.get("x_percent", 50)
        py = pos.get("y_percent", 50)

        roi = _roi_from_position(frame_w, frame_h, px, py, size_ratio=0.5)
        all_phases: list[dict] = []

        # ── 测量 visibility → opacity phases ──────────────────
        vis = measure_visibility(vpath, roi, sf, ef)
        if vis:
            vals = [v["value"] for v in vis]
            vis_phases = _detect_phases_from_curve(vals)
            for ph in vis_phases:
                start_f = sf + ph["start_idx"]
                end_f = sf + ph["end_idx"]
                seg_vals = vals[ph["start_idx"] : ph["end_idx"] + 1]
                easing = _sample_to_easing(seg_vals, ph["phase"] == "enter")
                all_phases.append({
                    "phase": ph["phase"],
                    "start_frame": start_f,
                    "end_frame": end_f,
                    "property": "opacity",
                    "from_value": ph["from_value"],
                    "to_value": ph["to_value"],
                    "easing": easing,
                    "note": f"{ph['phase']} opacity {ph['from_value']}→{ph['to_value']}",
                })

        # ── 测量位移 → translateX_px phases ──────────────────
        disp = measure_displacement(vpath, roi, sf, ef)
        if disp:
            dx_vals = [d["dx"] for d in disp]
            dx_phases = _detect_phases_from_curve(dx_vals)
            for ph in dx_phases:
                if abs(ph["to_value"] - ph["from_value"]) < 3:
                    continue
                start_f = sf + ph["start_idx"]
                end_f = sf + ph["end_idx"]
                seg_vals = dx_vals[ph["start_idx"] : ph["end_idx"] + 1]
                easing = _sample_to_easing(seg_vals, ph["phase"] == "enter")
                all_phases.append({
                    "phase": ph["phase"],
                    "start_frame": start_f,
                    "end_frame": end_f,
                    "property": "translateX_px",
                    "from_value": round(ph["from_value"]),
                    "to_value": round(ph["to_value"]),
                    "easing": easing,
                    "note": f"{ph['phase']} translateX {ph['from_value']:.0f}→{ph['to_value']:.0f}",
                })

        # ── 测量缩放 → scale phases ──────────────────────────
        scale_samples = measure_scale(vpath, roi, sf, ef)
        if scale_samples:
            sc_vals = [s["scale"] for s in scale_samples]
            sc_phases = _detect_phases_from_curve(sc_vals)
            for ph in sc_phases:
                if abs(ph["to_value"] - ph["from_value"]) < 0.05:
                    continue
                start_f = sf + ph["start_idx"]
                end_f = sf + ph["end_idx"]
                seg_vals = sc_vals[ph["start_idx"] : ph["end_idx"] + 1]
                easing = _sample_to_easing(seg_vals, ph["phase"] == "enter")
                all_phases.append({
                    "phase": ph["phase"],
                    "start_frame": start_f,
                    "end_frame": end_f,
                    "property": "scale",
                    "from_value": round(ph["from_value"], 3),
                    "to_value": round(ph["to_value"], 3),
                    "easing": easing,
                    "note": f"{ph['phase']} scale {ph['from_value']:.2f}→{ph['to_value']:.2f}",
                })

        # ── 测量打字速度 ─────────────────────────────────────
        is_typewriter = (eff == "typewriter" or "typewriter" in str(eff))
        if is_typewriter:
            cps = measure_typewriter_speed(vpath, roi, sf, ef, fps)
            if "typewriter" not in ep or not isinstance(ep.get("typewriter"), dict):
                ep["typewriter"] = {}
            ep["typewriter"]["chars_per_second"] = cps

        # ── 去除重复 phase（同一帧范围同一属性只保留一条）───
        deduped: list[dict] = []
        seen = set()
        for ph in all_phases:
            key = (ph["start_frame"], ph["end_frame"], ph["property"])
            if key not in seen:
                seen.add(key)
                deduped.append(ph)

        result_elements.append({
            "element_id": eid,
            "animation_phases": deduped,
            "effect_params": ep,
        })

    return {"elements": result_elements}
