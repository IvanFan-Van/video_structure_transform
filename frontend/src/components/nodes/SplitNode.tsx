import { BaseNode } from "../ui/BaseNode";
import { useVideoStore } from "../../store/useVideoStore";

interface Props {
    x: number;
    y: number;
    onPosChange: (id: string, x: number, y: number, w: number, h: number) => void;
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
    const videoErrors = useVideoStore((s) => s.videoErrors);
    const hasError = videoErrors.some((e) => e.nodeId === "split");

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
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
                {/* ── Config panels ── */}
                {!isSplitting && splitStatus !== "success" && (
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
                            <span>AI Detection</span>
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
                                        left: splitConfig.use_ai ? "19px" : "3px",
                                        bottom: "3px",
                                        background: "#fff",
                                        borderRadius: "50%",
                                        transition: "left 0.2s",
                                        boxShadow:
                                            "0 1px 3px rgba(0,0,0,0.15)",
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
                                    <span>Threshold</span>
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
                            <span>Min Scene Len</span>
                            <span
                                style={{ color: "#999", fontSize: "9px" }}
                            >
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
                {ready && (
                    <button
                        onClick={startSplit}
                        disabled={!compressResult}
                        style={{
                            padding: "6px 0",
                            fontSize: "10px",
                            fontFamily: "inherit",
                            fontWeight: 600,
                            letterSpacing: "2px",
                            color: "#fff",
                            background: compressResult
                                ? "#f97316"
                                : "#e0e0e0",
                            border: "none",
                            borderRadius: "4px",
                            cursor: compressResult
                                ? "pointer"
                                : "not-allowed",
                        }}
                    >
                        ▶ START SPLIT
                    </button>
                )}

                {isSplitting && (
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            gap: "6px",
                            padding: "8px 0",
                        }}
                    >
                        <div
                            className="split-loader"
                            style={{
                                width: "16px",
                                height: "16px",
                                border: "2px solid #e0e0e0",
                                borderTopColor: "#f97316",
                                borderRadius: "50%",
                                animation:
                                    "split-spin 0.8s linear infinite",
                            }}
                        />
                        <span
                            style={{
                                fontSize: "10px",
                                color: "#f97316",
                                fontWeight: 600,
                                letterSpacing: "2px",
                            }}
                        >
                            SPLITTING...
                        </span>
                        <button
                            onClick={stopSplit}
                            style={{
                                marginTop: "4px",
                                padding: "4px 12px",
                                fontSize: "9px",
                                fontFamily: "inherit",
                                color: "#ef4444",
                                background: "#fef2f2",
                                border: "1px solid #fecaca",
                                borderRadius: "4px",
                                cursor: "pointer",
                            }}
                        >
                            STOP
                        </button>
                    </div>
                )}

                {splitStatus === "success" && splitResult && (
                    <>
                        <div
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                                gap: "4px",
                                padding: "6px 0",
                                borderBottom: "1px solid #f0f0f0",
                            }}
                        >
                            <span
                                style={{
                                    fontSize: "10px",
                                    color: "#22c55e",
                                    fontWeight: 600,
                                    letterSpacing: "1px",
                                }}
                            >
                                ✓ SPLIT COMPLETE
                            </span>
                        </div>
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
                        <button
                            onClick={startSplit}
                            style={{
                                marginTop: "4px",
                                padding: "5px 0",
                                fontSize: "9px",
                                fontFamily: "inherit",
                                fontWeight: 600,
                                letterSpacing: "2px",
                                color: "#f97316",
                                background: "#fff7ed",
                                border: "1px solid #fed7aa",
                                borderRadius: "4px",
                                cursor: "pointer",
                            }}
                        >
                            RESTART
                        </button>
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

function SummaryKV({
    label,
    value,
}: {
    label: string;
    value: string;
}) {
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
            <span style={{ fontSize: "8px", color: "#bbb", letterSpacing: "1px" }}>
                {label}
            </span>
            <span style={{ fontSize: "10px", color: "#555", fontWeight: 600 }}>
                {value}
            </span>
        </div>
    );
}
