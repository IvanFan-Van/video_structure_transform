import { useState, useMemo } from "react";
import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
import { StatusHeader } from "../ui/StatusHeader";
import { AccordionItem } from "../ui/AccordionItem";
import { Tooltip } from "../ui/Tooltip";
import { VisualShot, VisualTextElement } from "../../store/types";

interface Props {
    x: number;
    y: number;
    onPosChange: (
        id: string,
        x: number,
        y: number,
        w: number,
        h: number,
    ) => void;
}

const PACING_LABELS: Record<string, string> = {
    fast: "Fast",
    medium: "Medium",
    slow: "Slow",
};

const CAMERA_LABELS: Record<string, string> = {
    static: "Static",
    zoom_in: "Zoom In",
    zoom_out: "Zoom Out",
    pan: "Pan",
    tilt: "Tilt",
    handheld: "Handheld",
};

const TRANSITION_LABELS: Record<string, string> = {
    cut: "Cut",
    dissolve: "Dissolve",
    wipe: "Wipe",
    fade_in: "Fade In",
    fade_out: "Fade Out",
};

const POSITION_LABELS: Record<string, string> = {
    top_center: "Top Center",
    center: "Center",
    bottom_center: "Bottom Center",
    overlay_left: "Overlay Left",
    overlay_right: "Overlay Right",
    full_screen: "Full Screen",
};

export function VisualAnalysisNode({ x, y, onPosChange }: Props) {
    const visualResult = useVideoStore((s) => s.visualResult);
    const visualStatus = useVideoStore((s) => s.visualStatus);
    const [expandedShots, setExpandedShots] = useState<Record<number, boolean>>(
        {},
    );

    const toggleShot = (index: number) => {
        setExpandedShots((prev) => ({
            ...prev,
            [index]: !prev[index],
        }));
    };

    const shotTextMap = useMemo(() => {
        const map: Record<number, VisualTextElement[]> = {};
        if (!visualResult?.text_elements) return map;
        for (const shot of visualResult.shots) {
            const matches = visualResult.text_elements.filter(
                (el) =>
                    el.appear_time < shot.end_time &&
                    el.disappear_time > shot.start_time,
            );
            if (matches.length > 0) map[shot.shot_index] = matches;
        }
        return map;
    }, [visualResult]);

    const hasData = visualStatus !== "idle" && visualStatus !== "cancelled";
    const accent = "#06b6d4";

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Visual Analysis"
            active={hasData}
            accent={accent}
            id="visual_analysis"
            tourId="visual_analysis"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "6px" }}
            >
                {!visualResult &&
                    (visualStatus === "idle" ||
                        visualStatus === "cancelled") && (
                        <StatusHeader
                            variant="idle"
                            label="Waiting for extraction..."
                        />
                    )}

                {!visualResult && visualStatus === "loading" && (
                    <StatusHeader
                        variant="loading"
                        label="Analyzing..."
                        accent={accent}
                    />
                )}

                {visualResult && (
                    <>
                        <StatusHeader
                            variant="success"
                            label="ANALYZED"
                            accent={accent}
                        />

                        {/* Pacing Summary */}
                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: "4px",
                                fontSize: "10px",
                            }}
                        >
                            <div
                                style={{
                                    background: "#f8f8f8",
                                    borderRadius: "3px",
                                    padding: "5px 7px",
                                    display: "flex",
                                    flexDirection: "column",
                                    alignItems: "center",
                                }}
                            >
                                <Tooltip
                                    tip={{
                                        en: "Shot pacing: Fast (<2s avg) / Medium (2-4s) / Slow (>4s), based on average shot duration",
                                        zh: "镜头切换节奏：Fast(快) Medium(中) Slow(慢)，基于平均镜头时长判断",
                                    }}
                                    inline
                                >
                                    <span
                                        style={{
                                            fontSize: "7px",
                                            color: "#bbb",
                                            letterSpacing: "1px",
                                        }}
                                    >
                                        PACE
                                    </span>
                                </Tooltip>
                                <span
                                    style={{
                                        fontWeight: 700,
                                        color: "#333",
                                        fontSize: "10px",
                                    }}
                                >
                                    {PACING_LABELS[
                                        visualResult.pacing.pacing_category
                                    ] || visualResult.pacing.pacing_category}
                                </span>
                            </div>
                            <div
                                style={{
                                    background: "#f8f8f8",
                                    borderRadius: "3px",
                                    padding: "5px 7px",
                                    display: "flex",
                                    flexDirection: "column",
                                    alignItems: "center",
                                }}
                            >
                                <Tooltip
                                    tip={{
                                        en: "Average duration per shot (seconds), used to assess editing rhythm",
                                        zh: "平均每个镜头的时长（秒），用于判断剪辑节奏",
                                    }}
                                    inline
                                >
                                    <span
                                        style={{
                                            fontSize: "7px",
                                            color: "#bbb",
                                            letterSpacing: "1px",
                                        }}
                                    >
                                        AVG SHOT
                                    </span>
                                </Tooltip>
                                <span
                                    style={{
                                        fontWeight: 700,
                                        color: "#333",
                                        fontSize: "10px",
                                    }}
                                >
                                    {visualResult.pacing.avg_shot_duration.toFixed(
                                        2,
                                    )}
                                    s
                                </span>
                            </div>
                            <div
                                style={{
                                    background: "#f8f8f8",
                                    borderRadius: "3px",
                                    padding: "5px 7px",
                                    display: "flex",
                                    flexDirection: "column",
                                    alignItems: "center",
                                    gridColumn: "1 / -1",
                                }}
                            >
                                <span
                                    style={{
                                        fontSize: "7px",
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                    }}
                                >
                                    DURATION
                                </span>
                                <span
                                    style={{
                                        fontWeight: 700,
                                        color: "#333",
                                        fontSize: "10px",
                                    }}
                                >
                                    {visualResult.total_duration.toFixed(1)}s
                                </span>
                            </div>
                        </div>

                        {/* Shots */}
                        <div
                            style={{
                                fontSize: "7px",
                                fontWeight: 600,
                                letterSpacing: "1px",
                                color: "#bbb",
                                marginBottom: "-2px",
                            }}
                        >
                            SHOTS
                        </div>
                        {visualResult.shots.map((shot: VisualShot) => {
                            const open =
                                expandedShots[shot.shot_index] ?? false;
                            const transition = visualResult.transitions.find(
                                (t) => t.after_shot_index === shot.shot_index,
                            );
                            return (
                                <AccordionItem
                                    key={shot.shot_index}
                                    open={open}
                                    onToggle={() => toggleShot(shot.shot_index)}
                                    title={
                                        <div
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            <span
                                                style={{
                                                    color: open
                                                        ? "#0891b2"
                                                        : "#555",
                                                }}
                                            >
                                                Shot #{shot.shot_index}
                                            </span>
                                            {shot.is_text_frame && (
                                                <span
                                                    style={{
                                                        fontSize: "7px",
                                                        background: "#fef3c7",
                                                        color: "#92400e",
                                                        padding: "1px 4px",
                                                        borderRadius: "2px",
                                                    }}
                                                >
                                                    TEXT
                                                </span>
                                            )}
                                        </div>
                                    }
                                    subtitle={`${shot.start_time.toFixed(1)}s \u2014 ${shot.end_time.toFixed(1)}s`}
                                    accent={accent}
                                    accentBg="#ecfeff"
                                    accentBorder="#cffafe"
                                >
                                    <div style={{ marginBottom: "6px" }}>
                                        <div
                                            style={{
                                                fontSize: "7px",
                                                fontWeight: 600,
                                                letterSpacing: "1px",
                                                color: "#bbb",
                                                marginBottom: "3px",
                                            }}
                                        >
                                            DESCRIPTION
                                        </div>
                                        <div style={{ color: "#333" }}>
                                            {shot.description || "(empty)"}
                                        </div>
                                    </div>
                                    <div
                                        style={{
                                            display: "flex",
                                            flexDirection: "column",
                                            gap: "3px",
                                        }}
                                    >
                                        {shot.camera_movement && (
                                            <div
                                                style={{
                                                    display: "flex",
                                                    justifyContent:
                                                        "space-between",
                                                    alignItems: "center",
                                                }}
                                            >
                                                <span
                                                    style={{
                                                        fontSize: "7px",
                                                        fontWeight: 600,
                                                        letterSpacing: "1px",
                                                        color: "#bbb",
                                                    }}
                                                >
                                                    CAMERA
                                                </span>
                                                <span
                                                    style={{
                                                        fontSize: "7px",
                                                        color: "#555",
                                                    }}
                                                >
                                                    {CAMERA_LABELS[
                                                        shot.camera_movement
                                                    ] || shot.camera_movement}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                    {transition && (
                                        <div
                                            style={{
                                                marginTop: "6px",
                                                padding: "4px 6px",
                                                background: "#f0fdfa",
                                                borderRadius: "2px",
                                                fontSize: "7px",
                                                color: "#0f766e",
                                            }}
                                        >
                                            Transition{" "}
                                            {TRANSITION_LABELS[
                                                transition.type
                                            ] || transition.type}
                                            {transition.duration > 0 &&
                                                ` (${transition.duration.toFixed(1)}s)`}
                                        </div>
                                    )}

                                    {/* Text elements in this shot */}
                                    {shotTextMap[shot.shot_index]?.map(
                                        (el, ei) => (
                                            <div
                                                key={ei}
                                                style={{
                                                    marginTop: "6px",
                                                    padding: "4px 6px",
                                                    background: "#f5f3ff",
                                                    borderRadius: "3px",
                                                    border: "1px solid #ede9fe",
                                                }}
                                            >
                                                <div
                                                    style={{
                                                        fontSize: "8px",
                                                        color: "#333",
                                                        lineHeight: "1.4",
                                                        marginBottom: "3px",
                                                    }}
                                                >
                                                    {el.text.length > 40
                                                        ? el.text.slice(0, 40) +
                                                          "…"
                                                        : el.text}
                                                </div>
                                                <div
                                                    style={{
                                                        display: "flex",
                                                        flexWrap: "wrap",
                                                        gap: "2px 8px",
                                                        fontSize: "7px",
                                                        color: "#888",
                                                    }}
                                                >
                                                    {el.position && (
                                                        <span>
                                                            {POSITION_LABELS[
                                                                el.position
                                                            ] || el.position}
                                                        </span>
                                                    )}
                                                    {el.font_weight && (
                                                        <span>
                                                            {el.font_weight}
                                                        </span>
                                                    )}
                                                    {el.font_size != null && (
                                                        <span>
                                                            {el.font_size}px
                                                        </span>
                                                    )}
                                                    {el.font_color && (
                                                        <span
                                                            style={{
                                                                display:
                                                                    "inline-flex",
                                                                alignItems:
                                                                    "center",
                                                                gap: "3px",
                                                            }}
                                                        >
                                                            <span
                                                                style={{
                                                                    display:
                                                                        "inline-block",
                                                                    width: "8px",
                                                                    height: "8px",
                                                                    borderRadius:
                                                                        "2px",
                                                                    background:
                                                                        el.font_color,
                                                                    border: "1px solid #ddd",
                                                                }}
                                                            />
                                                            {el.font_color}
                                                        </span>
                                                    )}
                                                    <span>
                                                        {el.appear_time.toFixed(
                                                            1,
                                                        )}
                                                        s —{" "}
                                                        {el.disappear_time.toFixed(
                                                            1,
                                                        )}
                                                        s
                                                    </span>
                                                </div>
                                            </div>
                                        ),
                                    )}
                                </AccordionItem>
                            );
                        })}
                    </>
                )}
            </div>
        </BaseNode>
    );
}
