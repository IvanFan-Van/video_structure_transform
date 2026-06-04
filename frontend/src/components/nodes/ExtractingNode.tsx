import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";

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

const TODO_ITEMS = [
    { key: "script", label: "Analyze Script Structure" },
    { key: "bgm", label: "Analyze BGM Features" },
    { key: "features", label: "Analyze Video Features" },
] as const;

const STATUS_CONFIG: Record<
    string,
    {
        icon: string;
        color: string;
        text: string;
        spin?: boolean;
        shimmer?: boolean;
    }
> = {
    pending: { icon: "○", color: "#ccc", text: "pending" },
    loading: {
        icon: "◌",
        color: "#555",
        text: "in progress",
        spin: true,
        shimmer: true,
    },
    done: { icon: "●", color: "#22c55e", text: "completed" },
    error: { icon: "✕", color: "#ef4444", text: "failed" },
};

const STYLE_ID = "extracting-node-animations";

function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
    @keyframes extractSpin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes extractShimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
  `;
    document.head.appendChild(style);
}

export function ExtractingNode({ x, y, onPosChange }: Props) {
    const compressResult = useVideoStore((s) => s.compressResult);
    const isExtractingFlow = useVideoStore((s) => s.isExtractingFlow);
    const scriptStatus = useVideoStore((s) => s.scriptStatus);
    const scriptTime = useVideoStore((s) => s.scriptTime);
    const startExtractScript = useVideoStore((s) => s.startExtractScript);
    const stopExtractScript = useVideoStore((s) => s.stopExtractScript);
    const videoErrors = useVideoStore((s) => s.videoErrors);
    const hasError = videoErrors.some((e) => e.nodeId === "extracting");

    injectStyles();

    const getStatus = (key: string) => {
        if (key === "script") return scriptStatus;
        if (key === "features") return "error";
        return "pending";
    };

    const formatTime = (t: number | null) => {
        if (t == null) return "";
        return ` (${t.toFixed(2)}s)`;
    };

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Extracting"
            active={!!compressResult}
            accent="#7c3aed"
            error={hasError}
            id="extracting"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
                {!isExtractingFlow && (
                    <button
                        onClick={startExtractScript}
                        disabled={!compressResult}
                        style={{
                            padding: "10px",
                            fontSize: "11px",
                            fontWeight: 600,
                            fontFamily: "inherit",
                            letterSpacing: "1px",
                            background: compressResult ? "#333" : "#e8e8e8",
                            color: compressResult ? "#fff" : "#bbb",
                            border: "none",
                            borderRadius: "3px",
                            cursor: compressResult ? "pointer" : "not-allowed",
                        }}
                    >
                        ▶ START EXTRACTING
                    </button>
                )}

                {isExtractingFlow && (
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "6px",
                        }}
                    >
                        {TODO_ITEMS.map((item) => {
                            const status = getStatus(item.key);
                            const cfg =
                                STATUS_CONFIG[status] || STATUS_CONFIG.pending;
                            const timeLabel =
                                item.key === "script"
                                    ? formatTime(scriptTime)
                                    : "";

                            return (
                                <div
                                    key={item.key}
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "space-between",
                                        fontSize: "9px",
                                        padding: "6px 8px",
                                        borderRadius: "3px",
                                        border:
                                            status === "loading"
                                                ? "1px solid #e0e0e0"
                                                : "1px solid transparent",
                                        background: cfg.shimmer
                                            ? "linear-gradient(90deg, #fafafa 0%, #f0f0f0 40%, #fafafa 70%)"
                                            : "transparent",
                                        backgroundSize: cfg.shimmer
                                            ? "400% 100%"
                                            : undefined,
                                        animation: cfg.shimmer
                                            ? "extractShimmer 1.8s ease-in-out infinite"
                                            : undefined,
                                    }}
                                >
                  <span
                    style={{
                      color: cfg.color,
                      fontSize: '10px',
                      marginRight: '8px',
                      fontWeight: 700,
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '14px',
                      height: '14px',
                      ...(cfg.spin ? { animation: 'extractSpin 1s linear infinite' } : {}),
                    }}
                  >
                    {cfg.icon}
                  </span>
                                    <span
                                        style={{
                                            flex: 1,
                                            color:
                                                status === "done"
                                                    ? "#555"
                                                    : status === "error"
                                                      ? "#ef4444"
                                                      : status === "loading"
                                                        ? "#333"
                                                        : "#bbb",
                                            fontWeight:
                                                status === "loading"
                                                    ? 600
                                                    : 400,
                                        }}
                                    >
                                        {item.label}
                                    </span>
                                    <span
                                        style={{
                                            color: cfg.color,
                                            fontSize: "8px",
                                        }}
                                    >
                                        {cfg.text}
                                        {timeLabel}
                                    </span>
                                </div>
                            );
                        })}

                        <button
                            onClick={stopExtractScript}
                            style={{
                                padding: "5px",
                                fontSize: "9px",
                                fontFamily: "inherit",
                                background: "transparent",
                                border: "1px solid #e0e0e0",
                                borderRadius: "3px",
                                color: "#999",
                                cursor: "pointer",
                                marginTop: "2px",
                            }}
                        >
                            ■ STOP
                        </button>
                    </div>
                )}
            </div>
        </BaseNode>
    );
}
