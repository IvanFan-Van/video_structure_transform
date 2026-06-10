import { BaseNode } from "../ui/BaseNode";
import { ActionButton } from "../ui/ActionButton";
import { StatusHeader } from "../ui/StatusHeader";
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

export function SplitNode({ x, y, onPosChange }: Props) {
    const compressResult = useVideoStore((s) => s.compressResult);
    const splitConfig = useVideoStore((s) => s.splitConfig);
    const setSplitConfig = useVideoStore((s) => s.setSplitConfig);
    const splitStatus = useVideoStore((s) => s.splitStatus);
    const isSplitting = useVideoStore((s) => s.isSplitting);
    const splitResult = useVideoStore((s) => s.splitResult);
    const startSplit = useVideoStore((s) => s.startSplit);
    const stopSplit = useVideoStore((s) => s.stopSplit);
    const { hasError } = useNodeError("split");

    const ready = !!compressResult && !isSplitting && splitStatus !== "loading";

    const sliderStyle: React.CSSProperties = {
        WebkitAppearance: "none",
        background: "#e8e8e8",
        borderRadius: "2px",
        outline: "none",
        width: "100%",
        height: "4px",
    };

    const totalDuration =
        splitResult?.segments.reduce((sum, s) => sum + s.duration, 0) ?? 0;

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Split"
            active={!!compressResult}
            accent="#f97316"
            error={hasError}
            id="split"
            tourId="split"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
                {/* ── Status Bar ── */}
                {splitStatus === "loading" && (
                    <StatusHeader
                        variant="loading"
                        label="SPLITTING..."
                        accent="#f97316"
                    />
                )}

                {splitStatus === "success" && (
                    <StatusHeader
                        variant="success"
                        label="SPLIT COMPLETE"
                        accent="#22c55e"
                    />
                )}

                {/* ── Config panels ── */}
                {!isSplitting && splitStatus !== "loading" && (
                    <>
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                fontSize: "10px",
                                color: "#555",
                            }}
                        >
                            <Tooltip tip={{ en: "Enable AI model for smart scene detection; disable for traditional algorithm (frame difference based)", zh: "开启后使用 AI 模型智能检测场景切换；关闭则使用传统算法（基于帧差异）" }} inline>
                                AI Detection
                            </Tooltip>
                            <label
                                style={{
                                    position: "relative",
                                    display: "inline-block",
                                    width: "36px",
                                    height: "20px",
                                }}
                            >
                                <input
                                    type="checkbox"
                                    checked={splitConfig.use_ai}
                                    onChange={(e) =>
                                        setSplitConfig({
                                            ...splitConfig,
                                            use_ai: e.target.checked,
                                        })
                                    }
                                    style={{
                                        opacity: 0,
                                        width: 0,
                                        height: 0,
                                    }}
                                />
                                <span
                                    style={{
                                        position: "absolute",
                                        cursor: "pointer",
                                        top: 0,
                                        left: 0,
                                        right: 0,
                                        bottom: 0,
                                        background: splitConfig.use_ai
                                            ? "#f97316"
                                            : "#ccc",
                                        borderRadius: "20px",
                                        transition: "background 0.2s",
                                    }}
                                />
                                <span
                                    style={{
                                        position: "absolute",
                                        height: "14px",
                                        width: "14px",
                                        left: splitConfig.use_ai
                                            ? "19px"
                                            : "3px",
                                        bottom: "3px",
                                        background: "#fff",
                                        borderRadius: "50%",
                                        transition: "left 0.2s",
                                        boxShadow: "0 1px 3px rgba(0,0,0,0.15)",
                                    }}
                                />
                            </label>
                        </div>

                        {!splitConfig.use_ai && (
                            <>
                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "space-between",
                                        fontSize: "10px",
                                        color: "#555",
                                    }}
                                >
                                    <Tooltip tip={{ en: "Detection sensitivity. Lower values = more sensitive, producing more and finer segments", zh: "检测敏感度。值越低越敏感，产生的片段更多更细" }} inline>
                                        Threshold
                                    </Tooltip>
                                    <span
                                        style={{
                                            color: "#999",
                                            fontSize: "9px",
                                        }}
                                    >
                                        {splitConfig.threshold.toFixed(1)}
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min={10}
                                    max={50}
                                    step={0.5}
                                    value={splitConfig.threshold}
                                    onChange={(e) =>
                                        setSplitConfig({
                                            ...splitConfig,
                                            threshold: parseFloat(
                                                e.target.value,
                                            ),
                                        })
                                    }
                                    style={sliderStyle}
                                />
                            </>
                        )}

                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                fontSize: "10px",
                                color: "#555",
                            }}
                        >
                            <Tooltip tip={{ en: "Minimum scene length in frames. Adjacent segments shorter than this are merged to avoid fragmentation", zh: "最短片段帧数。低于此长度的相邻片段会被合并，避免碎片化" }} inline>
                                Min Scene Len
                            </Tooltip>
                            <span style={{ color: "#999", fontSize: "9px" }}>
                                {splitConfig.min_scene_len} frames
                            </span>
                        </div>
                        <input
                            type="range"
                            min={5}
                            max={60}
                            step={1}
                            value={splitConfig.min_scene_len}
                            onChange={(e) =>
                                setSplitConfig({
                                    ...splitConfig,
                                    min_scene_len: parseInt(e.target.value, 10),
                                })
                            }
                            style={sliderStyle}
                        />
                    </>
                )}

                {/* ── START / STOP / RESTART button ── */}
                {ready && splitStatus === "idle" && (
                    <ActionButton
                        variant="primary"
                        label="▶ START SPLIT"
                        enabled={!!compressResult}
                        accent="#f97316"
                        onClick={startSplit}
                    />
                )}

                {isSplitting && (
                    <ActionButton
                        variant="muted"
                        label="■ STOP"
                        onClick={stopSplit}
                    />
                )}

                {splitStatus === "success" && splitResult && (
                    <>
                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: "4px",
                                fontSize: "10px",
                            }}
                        >
                            <SummaryKV
                                label="Method"
                                value={splitResult.method}
                            />
                            <SummaryKV
                                label="Segments"
                                value={String(splitResult.total_segments)}
                            />
                            <SummaryKV
                                label="Duration"
                                value={`${totalDuration.toFixed(1)}s`}
                            />
                        </div>
                        <ActionButton
                            variant="muted"
                            label="↻ RESTART"
                            onClick={startSplit}
                        />
                        <style
                            dangerouslySetInnerHTML={{
                                __html: `
                                    @keyframes split-spin {
                                        to { transform: rotate(360deg); }
                                    }
                                `,
                            }}
                        />
                    </>
                )}
            </div>
        </BaseNode>
    );
}

function SummaryKV({ label, value }: { label: string; value: string }) {
    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                padding: "4px",
                background: "#f9fafb",
                borderRadius: "4px",
            }}
        >
            <span
                style={{ fontSize: "8px", color: "#bbb", letterSpacing: "1px" }}
            >
                {label}
            </span>
            <span style={{ fontSize: "10px", color: "#555", fontWeight: 600 }}>
                {value}
            </span>
        </div>
    );
}
