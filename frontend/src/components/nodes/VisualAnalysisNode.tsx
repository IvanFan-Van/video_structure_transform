import { useState } from "react";
import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
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

const APPEAR_LABELS: Record<string, string> = {
    fade_in: "Fade In",
    pop: "Pop",
    slide: "Slide",
    typewriter: "Typewriter",
};

const EMPHASIS_LABELS: Record<string, string> = {
    zoom: "Zoom",
    shake: "Shake",
    color_change: "Color Change",
    stroke: "Stroke",
};

export function VisualAnalysisNode({ x, y, onPosChange }: Props) {
    const visualResult = useVideoStore((s) => s.visualResult);
    const visualStatus = useVideoStore((s) => s.visualStatus);
    const [expandedShots, setExpandedShots] = useState<
        Record<number, boolean>
    >({});

    const toggleShot = (index: number) => {
        setExpandedShots((prev) => ({
            ...prev,
            [index]: !prev[index],
        }));
    };

    const hasData = visualStatus !== "idle";
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
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "6px" }}
            >
                {!visualResult && visualStatus === "idle" && (
                    <div
                        style={{
                            fontSize: "9px",
                            color: "#bbb",
                            textAlign: "center",
                            padding: "12px 0",
                        }}
                    >
                        Waiting for extraction...
                    </div>
                )}

                {!visualResult && visualStatus === "loading" && (
                    <div
                        style={{
                            fontSize: "10px",
                            fontWeight: 600,
                            color: accent,
                            letterSpacing: "2px",
                            textAlign: "center",
                            padding: "12px 0",
                        }}
                    >
                        Analyzing...
                    </div>
                )}

                {visualResult && (
                    <>
                        <div
                            style={{
                                fontSize: "10px",
                                fontWeight: 600,
                                color: accent,
                                letterSpacing: "2px",
                                textAlign: "center",
                                marginBottom: "2px",
                            }}
                        >
                            ✓ ANALYZED
                        </div>

                        {/* Pacing Summary */}
                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: "4px",
                                fontSize: "10px",
                                marginBottom: "2px",
                            }}
                        >
                            {[
                                {
                                    label: "PACE",
                                    value: PACING_LABELS[
                                        visualResult.pacing.pacing_category
                                    ] || visualResult.pacing.pacing_category,
                                },
                                {
                                    label: "AVG SHOT",
                                    value: `${visualResult.pacing.avg_shot_duration.toFixed(1)}s`,
                                },
                                {
                                    label: "SHOTS",
                                    value: String(visualResult.shots.length),
                                },
                                {
                                    label: "DURATION",
                                    value: `${visualResult.total_duration?.toFixed(1)}s`,
                                },
                                {
                                    label: "TEXT EL.",
                                    value: String(
                                        visualResult.text_elements.length,
                                    ),
                                },
                                {
                                    label: "TRANS.",
                                    value: String(
                                        visualResult.transitions.length,
                                    ),
                                },
                            ].map(({ label, value }) => (
                                <div
                                    key={label}
                                    style={{
                                        background: "#f8f8f8",
                                        borderRadius: "3px",
                                        padding: "5px 7px",
                                    }}
                                >
                                    <div
                                        style={{
                                            fontSize: "7px",
                                            color: "#bbb",
                                            letterSpacing: "1px",
                                        }}
                                    >
                                        {label}
                                    </div>
                                    <div
                                        style={{
                                            fontWeight: 700,
                                            color: "#333",
                                            fontSize: "10px",
                                        }}
                                    >
                                        {value}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Shots */}
                        <div
                            style={{
                                fontSize: "7px",
                                fontWeight: 600,
                                letterSpacing: "1px",
                                color: "#bbb",
                                marginTop: "4px",
                                marginBottom: "2px",
                            }}
                        >
                            SHOTS
                        </div>
                        {visualResult.shots.map((shot: VisualShot) => {
                            const open = expandedShots[shot.shot_index] ?? false;
                            const transition = visualResult.transitions.find(
                                (t) => t.after_shot_index === shot.shot_index,
                            );
                            return (
                                <div key={shot.shot_index}>
                                    <div
                                        onClick={() =>
                                            toggleShot(shot.shot_index)
                                        }
                                        style={{
                                            display: "flex",
                                            justifyContent: "space-between",
                                            alignItems: "center",
                                            padding: "5px 8px",
                                            borderRadius: "3px",
                                            background: open
                                                ? "#ecfeff"
                                                : "#fafafa",
                                            border: open
                                                ? "1px solid #cffafe"
                                                : "1px solid #f0f0f0",
                                            cursor: "pointer",
                                            transition:
                                                "background 0.15s, border-color 0.15s",
                                        }}
                                    >
                                        <div
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "6px",
                                            }}
                                        >
                                            <span
                                                style={{
                                                    fontSize: "8px",
                                                    color: open
                                                        ? accent
                                                        : "#bbb",
                                                }}
                                            >
                                                {open ? "▼" : "▶"}
                                            </span>
                                            <span
                                                style={{
                                                    fontSize: "9px",
                                                    fontWeight: 600,
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
                                        <span
                                            style={{
                                                fontSize: "8px",
                                                color: "#bbb",
                                            }}
                                        >
                                            {shot.start_time.toFixed(1)}s —{" "}
                                            {shot.end_time.toFixed(1)}s
                                        </span>
                                    </div>
                                    {open && (
                                        <div
                                            style={{
                                                marginTop: "4px",
                                                padding: "8px",
                                                background: "#fafafa",
                                                borderRadius: "3px",
                                                border: "1px solid #f0f0f0",
                                                fontSize: "8px",
                                                color: "#555",
                                                lineHeight: "1.6",
                                            }}
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
                                                    {shot.description ||
                                                        "(empty)"}
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
                                                            alignItems:
                                                                "center",
                                                        }}
                                                    >
                                                        <span
                                                            style={{
                                                                fontSize:
                                                                    "7px",
                                                                fontWeight: 600,
                                                                letterSpacing:
                                                                    "1px",
                                                                color: "#bbb",
                                                            }}
                                                        >
                                                            CAMERA
                                                        </span>
                                                        <span
                                                            style={{
                                                                fontSize:
                                                                    "7px",
                                                                color: "#555",
                                                            }}
                                                        >
                                                            {CAMERA_LABELS[
                                                                shot
                                                                    .camera_movement
                                                            ] ||
                                                                shot.camera_movement}
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
                                        </div>
                                    )}
                                </div>
                            );
                        })}

                        {/* Text Elements */}
                        {visualResult.text_elements.length > 0 && (
                            <>
                                <div
                                    style={{
                                        fontSize: "7px",
                                        fontWeight: 600,
                                        letterSpacing: "1px",
                                        color: "#bbb",
                                        marginTop: "8px",
                                        marginBottom: "2px",
                                    }}
                                >
                                    TEXT ELEMENTS
                                </div>
                                {visualResult.text_elements.map(
                                    (el: VisualTextElement, idx: number) => (
                                        <div
                                            key={idx}
                                            style={{
                                                padding: "6px 8px",
                                                borderRadius: "3px",
                                                background: "#fafafa",
                                                border: "1px solid #f0f0f0",
                                                fontSize: "8px",
                                                color: "#555",
                                                lineHeight: "1.5",
                                            }}
                                        >
                                            <div
                                                style={{
                                                    fontWeight: 600,
                                                    color: "#333",
                                                    marginBottom: "3px",
                                                }}
                                            >
                                                {el.text}
                                            </div>
                                            <div
                                                style={{
                                                    display: "flex",
                                                    flexDirection: "column",
                                                    gap: "2px",
                                                    fontSize: "7px",
                                                }}
                                            >
                                                <div
                                                    style={{
                                                        display: "flex",
                                                        justifyContent:
                                                            "space-between",
                                                    }}
                                                >
                                                    <span style={{ color: "#bbb" }}>
                                                        POSITION
                                                    </span>
                                                    <span>
                                                        {el.position
                                                            ? POSITION_LABELS[
                                                                  el.position
                                                              ] || el.position
                                                            : "—"}
                                                    </span>
                                                </div>
                                                <div
                                                    style={{
                                                        display: "flex",
                                                        justifyContent:
                                                            "space-between",
                                                    }}
                                                >
                                                    <span style={{ color: "#bbb" }}>
                                                        APPEAR
                                                    </span>
                                                    <span>
                                                        {el.appear_style
                                                            ? APPEAR_LABELS[
                                                                  el.appear_style
                                                              ] ||
                                                              el.appear_style
                                                            : "—"}
                                                    </span>
                                                </div>
                                                {el.emphasis && (
                                                    <div
                                                        style={{
                                                            display: "flex",
                                                            justifyContent:
                                                                "space-between",
                                                        }}
                                                    >
                                                        <span
                                                            style={{
                                                                color: "#bbb",
                                                            }}
                                                        >
                                                            EMPHASIS
                                                        </span>
                                                        <span>
                                                            {EMPHASIS_LABELS[
                                                                el.emphasis
                                                            ] || el.emphasis}
                                                        </span>
                                                    </div>
                                                )}
                                                <div
                                                    style={{
                                                        display: "flex",
                                                        justifyContent:
                                                            "space-between",
                                                    }}
                                                >
                                                    <span style={{ color: "#bbb" }}>
                                                        TIME
                                                    </span>
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
                                        </div>
                                    ),
                                )}
                            </>
                        )}
                    </>
                )}
            </div>
        </BaseNode>
    );
}
