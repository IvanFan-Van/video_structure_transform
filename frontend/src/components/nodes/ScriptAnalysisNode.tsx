import { useState } from "react";
import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
import { StatusHeader } from "../ui/StatusHeader";
import { AccordionItem } from "../ui/AccordionItem";
import { Tooltip } from "../ui/Tooltip";
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
    const scriptStatus = useVideoStore((s) => s.scriptStatus);
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
            active={scriptStatus !== "idle" && scriptStatus !== "cancelled"}
            accent="#10b981"
            id="script_analysis"
            tourId="script_analysis"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "6px" }}
            >
                {!transcriptResult && (scriptStatus === "idle" || scriptStatus === "cancelled") && (
                    <StatusHeader variant="idle" label="Waiting for extraction..." />
                )}

                {!transcriptResult && scriptStatus === "loading" && (
                    <StatusHeader variant="loading" label="Analyzing..." accent="#10b981" />
                )}

                {transcriptResult && (
                    <>
                        <StatusHeader variant="success" label="ANALYZED" accent="#10b981" />
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
                                <AccordionItem
                                    key={key}
                                    open={open}
                                    onToggle={() => toggle(key)}
                                    title={label}
                                    subtitle={`${data.start_time.toFixed(1)}s \u2014 ${data.end_time.toFixed(1)}s`}
                                    accent="#10b981"
                                    accentBg="#ecfdf5"
                                    accentBorder="#a7f3d0"
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
                                                    <Tooltip tip={{ en: "Emotional tone of this stage: positive/negative/neutral/suspenseful", zh: "该阶段的情感基调：积极/消极/中性/悬疑" }} inline>
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
                                                    </Tooltip>
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
                                                    <Tooltip tip={{ en: "Hook type: pain_point/suspense/result_first/counter_intuitive/number_shock/identity_lock/scene_immersion/contrast_flip", zh: "开场钩子类型：痛点/悬念/结果前置/反直觉/数字冲击/身份锁定/场景沉浸/对比反转" }} inline>
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
                                                    </Tooltip>
                                                    <span
                                                        style={{
                                                            fontSize:
                                                                "7px",
                                                            color: "#555",
                                                        }}
                                                    >
                                                        {HOOK_TYPE_LABELS[
                                                            data
                                                                .hook_type
                                                        ] ||
                                                            data.hook_type}
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
                                                    <Tooltip tip={{ en: "CTA type: follow/like_collect/comment/purchase/discount_hook/dm_funnel/share_spread/challenge", zh: "行动号召类型：关注/点赞收藏/评论/购买/优惠钩子/私信引流/分享传播/挑战" }} inline>
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
                                                    </Tooltip>
                                                    <span
                                                        style={{
                                                            fontSize:
                                                                "7px",
                                                            color: "#555",
                                                        }}
                                                    >
                                                        {CTA_TYPE_LABELS[
                                                            data
                                                                .cta_type
                                                        ] ||
                                                            data.cta_type}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
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
