import { useState } from "react";
import { BaseNode } from "../ui/BaseNode";
import { ActionButton } from "../ui/ActionButton";
import { StatusHeader } from "../ui/StatusHeader";
import { AccordionItem } from "../ui/AccordionItem";
import { Tooltip } from "../ui/Tooltip";
import { useVideoStore } from "../../store/useVideoStore";
import { useNodeError } from "../../hooks/useNodeError";
import { NodeStatus } from "../../store/types";

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

const NODE_ID = "plan";

const STAGE_LABELS: Record<string, string> = {
    hook: "Hook",
    setup: "Setup",
    story: "Story",
    insight: "Insight",
    cta: "CTA",
    outro: "Outro",
};

function formatTime(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}

export function PlanNode({ x, y, onPosChange }: Props) {
    const { hasError } = useNodeError(NODE_ID);

    const planStatus = useVideoStore((s) => s.planStatus);
    const planTime = useVideoStore((s) => s.planTime);
    const planResult = useVideoStore((s) => s.planResult);
    const planableTaskIds = useVideoStore((s) => s.planableTaskIds);
    const effectTaskIds = useVideoStore((s) => s.effectTaskIds);
    const startPlan = useVideoStore((s) => s.startPlan);
    const stopPlan = useVideoStore((s) => s.stopPlan);

    const [userBrief, setUserBrief] = useState("");
    const [targetDuration, setTargetDuration] = useState("");
    const [bgmOpen, setBgmOpen] = useState(false);
    const [segmentOpen, setSegmentOpen] = useState<Record<number, boolean>>({});

    const toggleSegment = (i: number) =>
        setSegmentOpen((p) => ({ ...p, [i]: !p[i] }));

    const availableAnalyses: { label: string; ok: boolean }[] = [
        { label: "Script", ok: planableTaskIds.script != null },
        { label: "Visual", ok: planableTaskIds.visual != null },
        { label: "Audio", ok: planableTaskIds.audio != null },
    ];

    const effectCount = Object.values(effectTaskIds).filter(Boolean).length;
    if (effectCount > 0) {
        availableAnalyses.push({ label: `Effects (${effectCount})`, ok: true });
    }

    return (
        <BaseNode
            x={x}
            y={y}
            w={360}
            title="Plan"
            active={true}
            accent="#8b5cf6"
            error={hasError}
            id={NODE_ID}
            tourId="plan"
            onPosChange={onPosChange}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                    fontSize: "10px",
                }}
            >
                {/* ── Available analyses ── */}
                <div
                    style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "4px",
                    }}
                >
                    {availableAnalyses.map((a) => (
                        <span
                            key={a.label}
                            style={{
                                fontSize: "8px",
                                padding: "2px 7px",
                                borderRadius: "10px",
                                fontWeight: 600,
                                color: a.ok ? "#fff" : "#aaa",
                                background: a.ok ? "#8b5cf6" : "#f0f0f0",
                                border: a.ok
                                    ? "1px solid #7c3aed"
                                    : "1px solid #e0e0e0",
                                lineHeight: "1.6",
                            }}
                        >
                            {a.ok ? `✓ ${a.label}` : a.label}
                        </span>
                    ))}
                </div>

                {/* ── Idle state ── */}
                {(planStatus === "idle" || planStatus === "cancelled") && (
                    <>
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "4px",
                            }}
                        >
                            <Tooltip
                                tip={{
                                    en: "Describe your video topic, style and requirements. AI will generate a complete plan with narrative structure and shot breakdown.",
                                    zh: "描述你的视频主题、风格和需求，AI 会据此生成包含叙事结构和分镜的完整计划",
                                }}
                                inline
                            >
                                <span
                                    style={{
                                        fontSize: "8px",
                                        color: "#8b5cf6",
                                    }}
                                >
                                    Brief ?
                                </span>
                            </Tooltip>
                        </div>
                        <textarea
                            value={userBrief}
                            onChange={(e) => setUserBrief(e.target.value)}
                            placeholder="Describe your video topic and requirements..."
                            rows={3}
                            style={{
                                width: "100%",
                                padding: "6px 8px",
                                fontSize: "9px",
                                fontFamily: "inherit",
                                border: "1px solid #e0e0e0",
                                borderRadius: "4px",
                                resize: "vertical",
                                background: "#fafafa",
                                color: "#333",
                                outline: "none",
                                boxSizing: "border-box",
                            }}
                            onFocus={(e) =>
                                (e.currentTarget.style.borderColor = "#8b5cf6")
                            }
                            onBlur={(e) =>
                                (e.currentTarget.style.borderColor = "#e0e0e0")
                            }
                        />
                        <div
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                gap: "4px",
                            }}
                        >
                            <Tooltip
                                tip={{
                                    en: "Target video duration (seconds). Leave blank and AI will decide automatically.",
                                    zh: "目标视频时长（秒），留空由 AI 自动决定",
                                }}
                                inline
                            >
                                <span
                                    style={{
                                        fontSize: "8px",
                                        color: "#8b5cf6",
                                        whiteSpace: "nowrap",
                                    }}
                                >
                                    Duration ?
                                </span>
                            </Tooltip>
                            <input
                                type="number"
                                value={targetDuration}
                                onChange={(e) =>
                                    setTargetDuration(e.target.value)
                                }
                                placeholder="Duration (sec, optional)"
                                min={0}
                                step={1}
                                style={{
                                    width: "100%",
                                    padding: "4px 8px",
                                    fontSize: "9px",
                                    fontFamily: "inherit",
                                    border: "1px solid #e0e0e0",
                                    borderRadius: "4px",
                                    background: "#fafafa",
                                    color: "#333",
                                    outline: "none",
                                }}
                                onFocus={(e) =>
                                    (e.currentTarget.style.borderColor =
                                        "#8b5cf6")
                                }
                                onBlur={(e) =>
                                    (e.currentTarget.style.borderColor =
                                        "#e0e0e0")
                                }
                            />
                        </div>
                        <ActionButton
                            variant="primary"
                            label="▶ Generate Plan"
                            enabled={
                                userBrief.trim().length > 0 &&
                                (planableTaskIds.script != null ||
                                    planableTaskIds.visual != null)
                            }
                            onClick={() =>
                                startPlan(
                                    userBrief.trim(),
                                    targetDuration
                                        ? parseFloat(targetDuration)
                                        : undefined,
                                )
                            }
                        />
                    </>
                )}

                {/* ── Loading state ── */}
                {planStatus === "loading" && (
                    <>
                        <StatusHeader
                            variant="loading"
                            label="Generating plan..."
                            accent="#8b5cf6"
                        />
                        <ActionButton
                            variant="muted"
                            label="■ Stop"
                            onClick={stopPlan}
                        />
                        {planTime != null && (
                            <div
                                style={{
                                    fontSize: "8px",
                                    color: "#aaa",
                                    textAlign: "center",
                                }}
                            >
                                {planTime.toFixed(1)}s
                            </div>
                        )}
                    </>
                )}

                {/* ── Error state ── */}
                {planStatus === "error" && (
                    <StatusHeader
                        variant="error"
                        label="Plan generation failed"
                    />
                )}

                {/* ── Success state ── */}
                {planStatus === "success" && planResult && (
                    <>
                        <StatusHeader
                            variant="success"
                            label="Plan Generated"
                            accent="#8b5cf6"
                        />

                        <div
                            style={{
                                display: "flex",
                                flexWrap: "wrap",
                                gap: "2px 8px",
                                fontSize: "9px",
                                color: "#555",
                                lineHeight: "1.5",
                            }}
                        >
                            <span>
                                <span style={{ color: "#bbb" }}>
                                    Perspective:
                                </span>{" "}
                                {planResult.narrator_perspective}
                            </span>
                            <span>
                                <span style={{ color: "#bbb" }}>
                                    Est. Duration:
                                </span>{" "}
                                {String(planResult.estimated_duration)}s
                            </span>
                            <span>
                                <span style={{ color: "#bbb" }}>Segments:</span>{" "}
                                {planResult.segments.length}
                            </span>
                        </div>

                        <div
                            style={{
                                fontSize: "8px",
                                color: "#bbb",
                                wordBreak: "break-word",
                            }}
                        >
                            {planResult.plan_id.slice(0, 12)}...
                        </div>

                        {/* BGM spec */}
                        <AccordionItem
                            open={bgmOpen}
                            onToggle={() => setBgmOpen((o) => !o)}
                            title="BGM Spec"
                            accent="#8b5cf6"
                            accentBg="#f5f3ff"
                            accentBorder="#ddd6fe"
                        >
                            <div
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: "4px",
                                    fontSize: "9px",
                                    color: "#555",
                                    lineHeight: "1.5",
                                }}
                            >
                                <span>
                                    <span style={{ color: "#bbb" }}>
                                        Genre:
                                    </span>{" "}
                                    {planResult.bgm_spec.genre}
                                </span>
                                <span>
                                    <span style={{ color: "#bbb" }}>BPM:</span>{" "}
                                    {String(planResult.bgm_spec.bpm)}
                                </span>
                                <span>
                                    <span style={{ color: "#bbb" }}>Mood:</span>{" "}
                                    {planResult.bgm_spec.mood}
                                </span>
                            </div>
                        </AccordionItem>

                        {/* Segments */}
                        {planResult.segments.map((seg) => (
                            <AccordionItem
                                key={seg.index}
                                open={segmentOpen[seg.index] ?? false}
                                onToggle={() => toggleSegment(seg.index)}
                                title={
                                    <span>
                                        {STAGE_LABELS[seg.stage] ?? seg.stage}{" "}
                                        <span style={{ color: "#bbb" }}>
                                            ({formatTime(seg.start_time)} —{" "}
                                            {formatTime(seg.end_time)})
                                        </span>
                                    </span>
                                }
                                accent="#8b5cf6"
                                accentBg="#f5f3ff"
                                accentBorder="#ddd6fe"
                            >
                                <div
                                    style={{
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: "6px",
                                        fontSize: "9px",
                                    }}
                                >
                                    <div
                                        style={{
                                            color: "#666",
                                            lineHeight: "1.4",
                                        }}
                                    >
                                        {seg.narrative_intent}
                                    </div>
                                    {seg.slots.map((slot) => (
                                        <div
                                            key={slot.slot_id}
                                            style={{
                                                display: "flex",
                                                justifyContent: "space-between",
                                                alignItems: "center",
                                                gap: "6px",
                                                padding: "4px 6px",
                                                background: "#f9fafb",
                                                borderRadius: "3px",
                                                border: "1px solid #f0f0f0",
                                            }}
                                        >
                                            <div
                                                style={{
                                                    display: "flex",
                                                    flexDirection: "column",
                                                    gap: "2px",
                                                    minWidth: 0,
                                                    flex: 1,
                                                }}
                                            >
                                                <span
                                                    style={{
                                                        fontWeight: 600,
                                                        color: "#333",
                                                        fontSize: "8px",
                                                    }}
                                                >
                                                    {slot.slot_type}
                                                </span>
                                                <span
                                                    style={{
                                                        fontSize: "7px",
                                                        color: "#888",
                                                        overflow: "hidden",
                                                        textOverflow:
                                                            "ellipsis",
                                                        whiteSpace: "nowrap",
                                                    }}
                                                    title={slot.description}
                                                >
                                                    {slot.description}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </AccordionItem>
                        ))}

                        <ActionButton
                            variant="muted"
                            label="↻ Re-generate"
                            onClick={() =>
                                startPlan(
                                    userBrief.trim(),
                                    targetDuration
                                        ? parseFloat(targetDuration)
                                        : undefined,
                                )
                            }
                        />
                    </>
                )}
            </div>
        </BaseNode>
    );
}
