import { useState } from "react";
import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
import { TranscriptResult, TranscriptStage } from "../../store/types";

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

const STAGE_LABELS: Record<string, string> = {
    hook: "Hook",
    setup: "Setup",
    story: "Story",
    insight: "Insight",
    cta: "CTA",
    outro: "Outro",
};

const PERSPECTIVE_LABELS: Record<string, string> = {
    first_person: "First Person",
    second_person: "Second Person",
    third_person: "Third Person",
    mixed: "Mixed",
};

const EMOTIONAL_TONE_LABELS: Record<string, string> = {
    positive: "Positive",
    negative: "Negative",
    neutral: "Neutral",
    suspenseful: "Suspenseful",
};

const HOOK_TYPE_LABELS: Record<string, string> = {
    pain_point: "Pain Point",
    suspense: "Suspense",
    result_first: "Result First",
    counter_intuitive: "Counter-Intuitive",
    number_shock: "Number Shock",
    identity_lock: "Identity Lock",
    scene_immersion: "Scene Immersion",
    contrast_flip: "Contrast Flip",
};

const CTA_TYPE_LABELS: Record<string, string> = {
    follow: "Follow",
    like_collect: "Like & Collect",
    comment: "Comment",
    purchase: "Purchase",
    discount_hook: "Discount Hook",
    dm_funnel: "DM Funnel",
    share_spread: "Share & Spread",
    challenge: "Challenge",
};

export function ScriptAnalysisNode({ x, y, onPosChange }: Props) {
    const transcriptResult = useVideoStore((s) => s.transcriptResult);
    const [expanded, setExpanded] = useState<Record<string, boolean>>({});

    const stages: { key: string; label: string; data: TranscriptStage }[] = [];
    if (transcriptResult) {
        const s = transcriptResult.stages;
        for (const key of Object.keys(STAGE_LABELS)) {
            const data = s[key as keyof typeof s];
            if (data) {
                stages.push({ key, label: STAGE_LABELS[key], data });
            }
        }
    }

    const toggle = (key: string) => {
        setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
    };

    const perspectiveLabel = transcriptResult
        ? PERSPECTIVE_LABELS[transcriptResult.narrator_perspective ?? ""] ||
          transcriptResult.narrator_perspective
        : null;

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Script Analysis"
            active={!!transcriptResult}
            accent="#8b5cf6"
            id="script_analysis"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "6px" }}
            >
                {!transcriptResult && (
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

                {transcriptResult && (
                    <>
                        <div
                            style={{
                                fontSize: "10px",
                                fontWeight: 600,
                                color: "#8b5cf6",
                                letterSpacing: "2px",
                                textAlign: "center",
                                marginBottom: "2px",
                            }}
                        >
                            ✓ ANALYZED
                        </div>
                        {perspectiveLabel && (
                            <div
                                style={{
                                    fontSize: "8px",
                                    color: "#999",
                                    textAlign: "center",
                                    lineHeight: "1.4",
                                }}
                            >
                                Narrator:{" "}
                                <span
                                    style={{ color: "#666", fontWeight: 600 }}
                                >
                                    {perspectiveLabel}
                                </span>
                                {transcriptResult.narrator_perspective_note && (
                                    <span
                                        style={{
                                            display: "block",
                                            color: "#bbb",
                                        }}
                                    >
                                        {
                                            transcriptResult.narrator_perspective_note
                                        }
                                    </span>
                                )}
                            </div>
                        )}
                        {stages.map(({ key, label, data }) => {
                            const open = expanded[key] ?? false;
                            return (
                                <div key={key}>
                                    <div
                                        onClick={() => toggle(key)}
                                        style={{
                                            display: "flex",
                                            justifyContent: "space-between",
                                            alignItems: "center",
                                            padding: "6px 8px",
                                            borderRadius: "3px",
                                            background: open
                                                ? "#f5f3ff"
                                                : "#fafafa",
                                            border: open
                                                ? "1px solid #e9d5ff"
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
                                                        ? "#8b5cf6"
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
                                                        ? "#6d28d9"
                                                        : "#555",
                                                }}
                                            >
                                                {label}
                                            </span>
                                        </div>
                                        <span
                                            style={{
                                                fontSize: "8px",
                                                color: "#bbb",
                                            }}
                                        >
                                            {data.start_time.toFixed(1)}s —{" "}
                                            {data.end_time.toFixed(1)}s
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
                                            <div
                                                style={{ marginBottom: "6px" }}
                                            >
                                                <div
                                                    style={{
                                                        fontSize: "7px",
                                                        fontWeight: 600,
                                                        letterSpacing: "1px",
                                                        color: "#bbb",
                                                        marginBottom: "3px",
                                                    }}
                                                >
                                                    VISUAL TEXT
                                                </div>
                                                <div
                                                    style={{
                                                        color: "#333",
                                                        whiteSpace: "pre-wrap",
                                                    }}
                                                >
                                                    {data.visual_text ||
                                                        "(empty)"}
                                                </div>
                                            </div>
                                            <div
                                                style={{ marginBottom: "6px" }}
                                            >
                                                <div
                                                    style={{
                                                        fontSize: "7px",
                                                        fontWeight: 600,
                                                        letterSpacing: "1px",
                                                        color: "#bbb",
                                                        marginBottom: "3px",
                                                    }}
                                                >
                                                    AUDIO TEXT
                                                </div>
                                                <div
                                                    style={{
                                                        color: "#333",
                                                        whiteSpace: "pre-wrap",
                                                    }}
                                                >
                                                    {data.audio_text ||
                                                        "(empty)"}
                                                </div>
                                            </div>
                                            {(data.emotional_tone ||
                                                data.hook_type ||
                                                data.cta_type) && (
                                                <div
                                                    style={{
                                                        display: "flex",
                                                        flexDirection: "column",
                                                        gap: "3px",
                                                    }}
                                                >
                                                    {data.emotional_tone && (
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
                                                                EMOTIONAL TONE
                                                            </span>
                                                            <span
                                                                style={{
                                                                    fontSize:
                                                                        "7px",
                                                                    color: "#555",
                                                                }}
                                                            >
                                                                {EMOTIONAL_TONE_LABELS[
                                                                    data
                                                                        .emotional_tone
                                                                ] ||
                                                                    data.emotional_tone}
                                                            </span>
                                                        </div>
                                                    )}
                                                    {data.hook_type && (
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
                                                                HOOK TYPE
                                                            </span>
                                                            <span
                                                                style={{
                                                                    fontSize:
                                                                        "7px",
                                                                    color: "#555",
                                                                }}
                                                            >
                                                                {HOOK_TYPE_LABELS[
                                                                    data.hook_type
                                                                ] || data.hook_type}
                                                            </span>
                                                        </div>
                                                    )}
                                                    {data.cta_type && (
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
                                                                CTA TYPE
                                                            </span>
                                                            <span
                                                                style={{
                                                                    fontSize:
                                                                        "7px",
                                                                    color: "#555",
                                                                }}
                                                            >
                                                                {CTA_TYPE_LABELS[
                                                                    data.cta_type
                                                                ] || data.cta_type}
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </>
                )}
            </div>
        </BaseNode>
    );
}
