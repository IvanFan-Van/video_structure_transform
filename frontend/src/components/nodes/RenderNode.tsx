import { useMemo } from "react";
import { BaseNode } from "../ui/BaseNode";
import { ActionButton } from "../ui/ActionButton";
import { StatusHeader } from "../ui/StatusHeader";
import { CoverImage } from "../ui/CoverImage";
import { Tooltip } from "../ui/Tooltip";
import { useVideoStore } from "../../store/useVideoStore";
import { useNodeError } from "../../hooks/useNodeError";

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

const NODE_ID = "render";
const ACCENT = "#8b5cf6";

const PHASES: { key: string; label: string }[] = [
    { key: "loading", label: "Loading plan data" },
    { key: "bgm", label: "Loading BGM audio" },
    { key: "building", label: "Building render config" },
    { key: "rendering", label: "Rendering frames" },
    { key: "saving", label: "Saving output video" },
];

export function RenderNode({ x, y, onPosChange }: Props) {
    const { hasError } = useNodeError(NODE_ID);

    const planResult = useVideoStore((s) => s.planResult);
    const renderStatus = useVideoStore((s) => s.renderStatus);
    const renderResult = useVideoStore((s) => s.renderResult);
    const renderPhase = useVideoStore((s) => s.renderPhase);
    const renderProgress = useVideoStore((s) => s.renderProgress);
    const renderFrame = useVideoStore((s) => s.renderFrame);
    const renderTotalFrames = useVideoStore((s) => s.renderTotalFrames);
    const renderErrorMessage = useVideoStore((s) => s.renderErrorMessage);
    const startRender = useVideoStore((s) => s.startRender);
    const stopRender = useVideoStore((s) => s.stopRender);

    const hasFilledSlots = useMemo(() => {
        if (!planResult?.segments) return false;
        for (const seg of planResult.segments) {
            for (const slot of seg.slots) {
                if (slot.status === "filled") return true;
            }
        }
        return false;
    }, [planResult]);

    const enabled = !!planResult && hasFilledSlots;

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Render"
            active={enabled}
            accent={ACCENT}
            error={hasError}
            id={NODE_ID}
            tourId="render"
            onPosChange={onPosChange}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                }}
            >
                {/* ── Idle state ── */}
                {(renderStatus === "idle" ||
                    renderStatus === "cancelled" ||
                    renderStatus === "error") && (
                    <>
                        {renderStatus === "error" && (
                            <>
                                <StatusHeader
                                    variant="error"
                                    label="Render failed"
                                />
                                {renderErrorMessage && (
                                    <div
                                        style={{
                                            fontSize: "8px",
                                            color: "#ef4444",
                                            background: "#fef2f2",
                                            border: "1px solid #fecaca",
                                            borderRadius: "3px",
                                            padding: "6px 8px",
                                            wordBreak: "break-all",
                                            lineHeight: "1.4",
                                        }}
                                    >
                                        {renderErrorMessage}
                                    </div>
                                )}
                            </>
                        )}
                        <Tooltip
                            tip={
                                enabled
                                    ? { en: "Render the filled Plan template into a final video using the Remotion engine", zh: "基于已填充的 Plan 模板调用 Remotion 引擎渲染最终视频" }
                                    : planResult
                                      ? { en: "Fill material in Slot nodes first, or batch generate via Generate node", zh: "需先在 Slot 节点中填充素材，或通过 Generate 批量生成" }
                                      : { en: "Generate a Plan template first", zh: "需要先生成 Plan 模板" }
                            }
                        >
                            <ActionButton
                                variant="primary"
                                label="▶ RENDER"
                                enabled={enabled}
                                accent={ACCENT}
                                onClick={startRender}
                            />
                        </Tooltip>
                    </>
                )}

                {/* ── Loading state ── */}
                {renderStatus === "loading" && (
                    <>
                        <StatusHeader
                            variant="loading"
                            label="RENDERING"
                            accent={ACCENT}
                        />
                        <div
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                gap: "4px",
                                fontSize: "8px",
                            }}
                        >
                            {PHASES.map((p) => {
                                const isCurrent = renderPhase === p.key;
                                const isPast =
                                    renderPhase &&
                                    PHASES.findIndex(
                                        (x) => x.key === renderPhase,
                                    ) >
                                        PHASES.findIndex(
                                            (x) => x.key === p.key,
                                        );
                                return (
                                    <div
                                        key={p.key}
                                        style={{
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "6px",
                                            color:
                                                isCurrent || isPast
                                                    ? "#333"
                                                    : "#ccc",
                                            fontWeight:
                                                isCurrent ? 600 : 400,
                                        }}
                                    >
                                        <span
                                            style={{
                                                display: "inline-flex",
                                                width: "8px",
                                                height: "8px",
                                                borderRadius: "50%",
                                                background:
                                                    isCurrent
                                                        ? ACCENT
                                                        : isPast
                                                          ? "#999"
                                                          : "#e0e0e0",
                                                flexShrink: 0,
                                            }}
                                        />
                                        <span>{p.label}</span>
                                    </div>
                                );
                            })}
                        </div>

                        {renderPhase === "rendering" && (
                            <div
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: "4px",
                                }}
                            >
                                <div
                                    style={{
                                        width: "100%",
                                        height: "6px",
                                        background: "#f0f0f0",
                                        borderRadius: "3px",
                                        overflow: "hidden",
                                    }}
                                >
                                    <div
                                        style={{
                                            width: `${Math.min(renderProgress, 100)}%`,
                                            height: "100%",
                                            background: ACCENT,
                                            borderRadius: "3px",
                                            transition: "width 0.3s ease",
                                        }}
                                    />
                                </div>
                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        fontSize: "8px",
                                        color: "#888",
                                    }}
                                >
                                    <span>{renderProgress}%</span>
                                    <span>
                                        帧 {renderFrame} /{" "}
                                        {renderTotalFrames > 0
                                            ? renderTotalFrames
                                            : "..."}
                                    </span>
                                </div>
                            </div>
                        )}

                        <ActionButton
                            variant="muted"
                            label="■ STOP"
                            onClick={stopRender}
                        />
                    </>
                )}

                {/* ── Success state ── */}
                {renderStatus === "success" && renderResult && (
                    <>
                        <StatusHeader
                            variant="success"
                            label="RENDERED"
                            accent={ACCENT}
                        />
                        <CoverImage
                            coverImageAssetId={renderResult.asset_id}
                            videoAssetId={renderResult.asset_id}
                            alt="Rendered video cover"
                        />
                        <div
                            style={{
                                fontSize: "9px",
                                color: "#888",
                                lineHeight: "16px",
                            }}
                        >
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    borderBottom: "1px solid #f0f0f0",
                                    paddingBottom: "2px",
                                    marginBottom: "4px",
                                    color: "#bbb",
                                    fontSize: "8px",
                                    letterSpacing: "1px",
                                }}
                            >
                                Output Specs
                            </div>
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                }}
                            >
                                <span style={{ color: "#bbb" }}>duration</span>
                                <span style={{ color: "#333", fontWeight: 600 }}>
                                    {renderResult.duration.toFixed(1)}s
                                </span>
                            </div>
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                }}
                            >
                                <span style={{ color: "#bbb" }}>resolution</span>
                                <span style={{ color: "#333", fontWeight: 600 }}>
                                    {renderResult.width}×{renderResult.height}
                                </span>
                            </div>
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                }}
                            >
                                <span style={{ color: "#bbb" }}>fps</span>
                                <span style={{ color: "#333", fontWeight: 600 }}>
                                    {renderResult.fps}
                                </span>
                            </div>
                        </div>
                        <ActionButton
                            variant="muted"
                            label="RE-RENDER"
                            onClick={startRender}
                        />
                    </>
                )}
            </div>
        </BaseNode>
    );
}
