import { useState } from "react";
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
    const [expandedShots, setExpandedShots] = useState<Record<number, boolean>>(
        {},
    );

    const toggleShot = (index: number) => {
        setExpandedShots((prev) => ({
            ...prev,
            [index]: !prev[index],
        }));
    };

    const [expandedTextElements, setExpandedTextElements] = useState<
        Record<number, boolean>
    >({});
    const toggleTextElement = (idx: number) => {
        setExpandedTextElements((prev) => ({
            ...prev,
            [idx]: !prev[idx],
        }));
    };

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
                                <Tooltip tip="镜头切换节奏：Fast(快) Medium(中) Slow(慢)，基于平均镜头时长判断" inline>
                                <span
                                    style={{
                                        fontSize: "7px",
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                        cursor: "help",
                                        borderBottom: "1px dotted #ccc",
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
                                <Tooltip tip="平均每个镜头的时长（秒），用于判断剪辑节奏" inline>
                                <span
                                    style={{
                                        fontSize: "7px",
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                        cursor: "help",
                                        borderBottom: "1px dotted #ccc",
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
                                </AccordionItem>
                            );
                        })}

                        {/* Text Elements */}
                        <div
                            style={{
                                fontSize: "7px",
                                fontWeight: 600,
                                letterSpacing: "1px",
                                color: "#bbb",
                                marginTop: "4px",
                                marginBottom: "-2px",
                            }}
                        >
                            TEXT ELEMENTS
                        </div>
                        {visualResult.text_elements.map(
                            (el: VisualTextElement, idx: number) => {
                                const open = expandedTextElements[idx] ?? false;
                                const preview =
                                    el.text.length > 35
                                        ? el.text.slice(0, 35) + "..."
                                        : el.text;
                                return (
                                    <AccordionItem
                                        key={idx}
                                        open={open}
                                        onToggle={() => toggleTextElement(idx)}
                                        title={preview}
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
                                                FULL TEXT
                                            </div>
                                            <div
                                                style={{
                                                    color: "#333",
                                                    whiteSpace: "pre-wrap",
                                                }}
                                            >
                                                {el.text}
                                            </div>
                                        </div>
                                        {el.appear_time !== undefined && (
                                            <div
                                                style={{ marginBottom: "4px" }}
                                            >
                                                <span
                                                    style={{
                                                        fontSize: "7px",
                                                        color: "#bbb",
                                                    }}
                                                >
                                                    {el.appear_time.toFixed(1)}s
                                                    —{" "}
                                                    {el.disappear_time.toFixed(
                                                        1,
                                                    )}
                                                    s
                                                </span>
                                            </div>
                                        )}
                                        <div
                                            style={{
                                                display: "flex",
                                                flexDirection: "column",
                                                gap: "3px",
                                            }}
                                        >
                                            {el.position && (
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
                                                            letterSpacing:
                                                                "1px",
                                                            color: "#bbb",
                                                        }}
                                                    >
                                                        POSITION
                                                    </span>
                                                    <span
                                                        style={{
                                                            fontSize: "7px",
                                                            color: "#555",
                                                        }}
                                                    >
                                                        {POSITION_LABELS[
                                                            el.position
                                                        ] || el.position}
                                                    </span>
                                                </div>
                                            )}
                                            {el.appear_style && (
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
                                                            letterSpacing:
                                                                "1px",
                                                            color: "#bbb",
                                                        }}
                                                    >
                                                        APPEAR
                                                    </span>
                                                    <span
                                                        style={{
                                                            fontSize: "7px",
                                                            color: "#555",
                                                        }}
                                                    >
                                                        {APPEAR_LABELS[
                                                            el.appear_style
                                                        ] || el.appear_style}
                                                    </span>
                                                </div>
                                            )}
                                            {el.emphasis && (
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
                                                            letterSpacing:
                                                                "1px",
                                                            color: "#bbb",
                                                        }}
                                                    >
                                                        EMPHASIS
                                                    </span>
                                                    <span
                                                        style={{
                                                            fontSize: "7px",
                                                            color: "#555",
                                                        }}
                                                    >
                                                        {EMPHASIS_LABELS[
                                                            el.emphasis
                                                        ] || el.emphasis}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </AccordionItem>
                                );
                            },
                        )}
                    </>
                )}
            </div>
        </BaseNode>
    );
}
