import { useState, useRef } from "react";
import { BaseNode } from "../ui/BaseNode";
import { CoverImage } from "../ui/CoverImage";
import { ActionButton } from "../ui/ActionButton";
import { StatusHeader } from "../ui/StatusHeader";
import { AccordionItem } from "../ui/AccordionItem";
import { Tooltip } from "../ui/Tooltip";
import { EffectSearch } from "../effects/EffectSearch";
import { useVideoStore } from "../../store/useVideoStore";
import { useNodeError } from "../../hooks/useNodeError";
import { SplitSegment, SplitClipAsset } from "../../store/types";

interface Props {
    x: number;
    y: number;
    segment: SplitSegment;
    clip: SplitClipAsset | undefined;
    index: number;
    method: string;
    onPosChange: (
        id: string,
        x: number,
        y: number,
        w: number,
        h: number,
    ) => void;
}

export function EffectAnalysisNode({
    x,
    y,
    segment,
    clip,
    index,
    method,
    onPosChange,
}: Props) {
    const meta = clip?.metadata;
    const nodeId = `effect_segment_${index}`;
    const { hasError } = useNodeError(nodeId);

    const effectStatuses = useVideoStore((s) => s.effectStatuses);
    const effectResults = useVideoStore((s) => s.effectResults);
    const effectParamStatuses = useVideoStore((s) => s.effectParamStatuses);
    const effectParamResults = useVideoStore((s) => s.effectParamResults);
    const analyzeEffect = useVideoStore((s) => s.analyzeEffect);
    const analyzeEffectParams = useVideoStore((s) => s.analyzeEffectParams);
    const removeEffect = useVideoStore((s) => s.removeEffect);
    const addEffect = useVideoStore((s) => s.addEffect);

    const status = effectStatuses[index] ?? "idle";
    const result = effectResults[index] ?? null;
    const paramStatus = effectParamStatuses[index] ?? "idle";
    const paramResult = effectParamResults[index] ?? null;

    const [expandedObs, setExpandedObs] = useState(false);
    const [expandedEffects, setExpandedEffects] = useState(false);
    const [expandedParams, setExpandedParams] = useState(false);
    const [searchOpen, setSearchOpen] = useState(false);
    const addBtnRef = useRef<HTMLButtonElement>(null);

    return (
        <BaseNode
            x={x}
            y={y}
            w={260}
            title={`Segment ${index + 1}`}
            active={true}
            accent="#f97316"
            error={hasError}
            id={nodeId}
            tourId={nodeId}
            onPosChange={onPosChange}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    fontSize: "10px",
                }}
            >
                <CoverImage
                    coverImageAssetId={clip?.cover_image_asset_id}
                    videoAssetId={clip?.asset_id}
                    alt={`Segment ${index + 1} cover`}
                    maxHeight={80}
                />

                {/* ── Segment metadata ── */}
                <div
                    style={{
                        fontSize: "8px",
                        color: "#bbb",
                        letterSpacing: "1px",
                        fontWeight: 600,
                    }}
                >
                    {method === "ai" ? "AI" : "SCENEDETECT"}
                </div>

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
                        <span style={{ color: "#bbb" }}>Time:</span>{" "}
                        {segment.start_sec.toFixed(1)}s —{" "}
                        {segment.end_sec.toFixed(1)}s
                        <span style={{ color: "#bbb" }}>
                            {" "}
                            ({segment.duration.toFixed(1)}s)
                        </span>
                    </span>
                    {segment.cut_score != null && (
                        <span>
                            <span style={{ color: "#bbb" }}>Score:</span>{" "}
                            {segment.cut_score.toFixed(1)}
                        </span>
                    )}
                </div>

                {segment.reason != null && (
                    <div
                        style={{
                            fontSize: "9px",
                            color: "#555",
                            lineHeight: "1.4",
                            wordBreak: "break-word",
                        }}
                    >
                        <span style={{ color: "#bbb" }}>Reason:</span>{" "}
                        {segment.reason}
                    </div>
                )}

                {meta && (
                    <div
                        style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "2px 8px",
                            fontSize: "9px",
                            color: "#777",
                            lineHeight: "1.5",
                            paddingTop: "4px",
                            borderTop: "1px solid #f0f0f0",
                        }}
                    >
                        {meta.codec && (
                            <span>
                                <span style={{ color: "#bbb" }}>Codec:</span>{" "}
                                {meta.codec}
                            </span>
                        )}
                        {meta.width && meta.height && (
                            <span>
                                <span style={{ color: "#bbb" }}>Res:</span>{" "}
                                {meta.width}×{meta.height}
                            </span>
                        )}
                        {meta.fps != null && (
                            <span>
                                <span style={{ color: "#bbb" }}>FPS:</span>{" "}
                                {meta.fps.toFixed(1)}
                            </span>
                        )}
                        {clip?.asset_id && (
                            <span>
                                <span style={{ color: "#bbb" }}>Asset:</span>{" "}
                                {clip.asset_id.slice(0, 8)}...
                            </span>
                        )}
                    </div>
                )}

                {/* ── Effect analysis ── */}
                <div
                    style={{
                        paddingTop: "4px",
                        borderTop: "1px solid #f0f0f0",
                    }}
                >
                    {status === "idle" && (
                        <Tooltip
                            tip={{
                                en: "AI analyzes visual effects and editing techniques in this clip (transitions, filters, text animations, etc.)",
                                zh: "AI 分析该片段中的视觉特效和编辑手法（如转场、滤镜、文字动画等）",
                            }}
                        >
                            <ActionButton
                                variant="muted"
                                label="▶ Analyze Effects"
                                onClick={() =>
                                    clip?.asset_id &&
                                    analyzeEffect(clip.asset_id, index)
                                }
                            />
                        </Tooltip>
                    )}

                    {status === "loading" && (
                        <StatusHeader
                            variant="loading"
                            label="Analyzing effects..."
                            accent="#f97316"
                        />
                    )}

                    {status === "error" && (
                        <StatusHeader variant="error" label="Analysis failed" />
                    )}

                    {status === "success" && result && (
                        <div
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                gap: "6px",
                            }}
                        >
                            <StatusHeader
                                variant="success"
                                label="Effects Analyzed"
                                accent="#f97316"
                            />
                            <AccordionItem
                                open={expandedObs}
                                onToggle={() => setExpandedObs((o) => !o)}
                                title="Observations"
                                accent="#f97316"
                                accentBg="#fff7ed"
                                accentBorder="#fed7aa"
                            >
                                <div
                                    style={{
                                        color: "#333",
                                        lineHeight: "1.5",
                                        fontSize: "10px",
                                    }}
                                >
                                    {result.observations}
                                </div>
                            </AccordionItem>
                            <AccordionItem
                                open={expandedEffects}
                                onToggle={() => setExpandedEffects((o) => !o)}
                                title={`Effects (${result.effects.length})`}
                                accent="#f97316"
                                accentBg="#fff7ed"
                                accentBorder="#fed7aa"
                            >
                                <div
                                    style={{
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: "6px",
                                    }}
                                >
                                    {result.effects.map((ef, i) => (
                                        <div
                                            key={i}
                                            style={{
                                                display: "flex",
                                                flexDirection: "column",
                                                gap: "4px",
                                                padding: "6px 8px",
                                                background: "#f9fafb",
                                                borderRadius: "3px",
                                                border: "1px solid #f0f0f0",
                                                position: "relative",
                                            }}
                                        >
                                            <button
                                                onClick={() =>
                                                    removeEffect(index, i)
                                                }
                                                title="Remove effect"
                                                style={{
                                                    position: "absolute",
                                                    top: 2,
                                                    right: 4,
                                                    fontSize: "10px",
                                                    color: "#ccc",
                                                    background: "none",
                                                    border: "none",
                                                    cursor: "pointer",
                                                    padding: "0 2px",
                                                    lineHeight: 1,
                                                    fontFamily: "inherit",
                                                }}
                                                onMouseEnter={(e) =>
                                                    (e.currentTarget.style.color =
                                                        "#ef4444")
                                                }
                                                onMouseLeave={(e) =>
                                                    (e.currentTarget.style.color =
                                                        "#ccc")
                                                }
                                            >
                                                ×
                                            </button>
                                            <span
                                                style={{
                                                    fontWeight: 600,
                                                    color: "#333",
                                                    fontSize: "9px",
                                                    paddingRight: "12px",
                                                }}
                                            >
                                                {ef.name}
                                            </span>
                                            <span
                                                style={{
                                                    fontSize: "8px",
                                                    color: "#888",
                                                    lineHeight: "1.4",
                                                }}
                                            >
                                                {ef.evidence}
                                            </span>
                                        </div>
                                    ))}
                                    <button
                                        ref={addBtnRef}
                                        onClick={() => setSearchOpen(true)}
                                        style={{
                                            padding: "6px",
                                            background: "#f9fafb",
                                            border: "1px dashed #ddd",
                                            borderRadius: "3px",
                                            cursor: "pointer",
                                            fontSize: "10px",
                                            color: "#bbb",
                                            fontFamily: "inherit",
                                        }}
                                    >
                                        + Add effect
                                    </button>
                                </div>
                            </AccordionItem>
                            <ActionButton
                                variant="muted"
                                label="↻ Re-analyze"
                                onClick={() =>
                                    clip?.asset_id &&
                                    analyzeEffect(clip.asset_id, index)
                                }
                            />

                            {/* ── Step 3: Effect params analysis ── */}
                            {paramStatus === "idle" && (
                                <ActionButton
                                    variant="muted"
                                    label="▶ Analyze Params"
                                    onClick={() => {
                                        if (clip?.asset_id) {
                                            analyzeEffectParams(
                                                clip.asset_id,
                                                index,
                                                result.effects.map(
                                                    (e) => e.name,
                                                ),
                                            );
                                        }
                                    }}
                                />
                            )}

                            {paramStatus === "loading" && (
                                <StatusHeader
                                    variant="loading"
                                    label="Analyzing params..."
                                    accent="#f97316"
                                />
                            )}

                            {paramStatus === "error" && (
                                <StatusHeader
                                    variant="error"
                                    label="Params analysis failed"
                                />
                            )}

                            {paramStatus === "success" && paramResult && (
                                <>
                                    <StatusHeader
                                        variant="success"
                                        label="Params Analyzed"
                                        accent="#f97316"
                                    />
                                    <AccordionItem
                                        open={expandedParams}
                                        onToggle={() =>
                                            setExpandedParams((o) => !o)
                                        }
                                        title={`Params (${paramResult.param_set.length})`}
                                        accent="#f97316"
                                        accentBg="#fff7ed"
                                        accentBorder="#fed7aa"
                                    >
                                        <div
                                            style={{
                                                display: "flex",
                                                flexDirection: "column",
                                                gap: "5px",
                                            }}
                                        >
                                            {paramResult.param_set.map((p, i) => (
                                                <div
                                                    key={i}
                                                    style={{
                                                        padding: "5px 7px",
                                                        background: "#f9fafb",
                                                        borderRadius: "3px",
                                                        border: "1px solid #f0f0f0",
                                                        display: "flex",
                                                        flexDirection: "column",
                                                        gap: "3px",
                                                    }}
                                                >
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
                                                                fontWeight: 600,
                                                                color: "#333",
                                                                fontSize: "8px",
                                                            }}
                                                        >
                                                            {p.effect_name}
                                                        </span>
                                                        <span
                                                            style={{
                                                                fontSize:
                                                                    "6.5px",
                                                                color: "#888",
                                                                background:
                                                                    "#f0f0f0",
                                                                padding:
                                                                    "1px 4px",
                                                                borderRadius:
                                                                    "2px",
                                                            }}
                                                        >
                                                            {p.applies_to}
                                                        </span>
                                                    </div>
                                                    <div
                                                        style={{
                                                            fontSize: "7px",
                                                            color: "#888",
                                                            lineHeight: "1.4",
                                                        }}
                                                    >
                                                        {p.evidence}
                                                    </div>
                                                    <div
                                                        style={{
                                                            fontSize: "6.5px",
                                                            color: "#aaa",
                                                        }}
                                                    >
                                                        {p.timing_start.toFixed(
                                                            1,
                                                        )}
                                                        s —{" "}
                                                        {(
                                                            p.timing_start +
                                                            p.timing_duration
                                                        ).toFixed(1)}
                                                        s (
                                                        {p.timing_duration.toFixed(
                                                            1,
                                                        )}
                                                        s)
                                                    </div>
                                                    <div
                                                        style={{
                                                            fontSize: "6.5px",
                                                            color: "#666",
                                                            background:
                                                                "#f5f5f5",
                                                            padding: "3px 5px",
                                                            borderRadius: "2px",
                                                            fontFamily:
                                                                "'JetBrains Mono', monospace",
                                                            whiteSpace:
                                                                "pre-wrap",
                                                            lineHeight: "1.3",
                                                            maxHeight: "60px",
                                                            overflowY: "auto",
                                                        }}
                                                    >
                                                        {JSON.stringify(
                                                            p.remocn_props,
                                                            null,
                                                            2,
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </AccordionItem>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
            <EffectSearch
                open={searchOpen}
                onClose={() => setSearchOpen(false)}
                onSelect={(name) => {
                    addEffect(index, { name, evidence: "" });
                    setSearchOpen(false);
                }}
                triggerRef={addBtnRef}
            />
        </BaseNode>
    );
}
