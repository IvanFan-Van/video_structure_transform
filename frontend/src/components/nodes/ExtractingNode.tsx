import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
import { NodeStatus } from "../../store/types";
import { useNodeError } from "../../hooks/useNodeError";
import { ActionButton } from "../ui/ActionButton";

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
    NodeStatus,
    {
        icon: string;
        color: string;
        text: string;
        spin?: boolean;
        shimmer?: boolean;
    }
> = {
    idle: { icon: "○", color: "#ccc", text: "idle" },
    loading: {
        icon: "◌",
        color: "#555",
        text: "in progress",
        spin: true,
        shimmer: true,
    },
    success: { icon: "●", color: "#22c55e", text: "completed" },
    error: { icon: "✕", color: "#ef4444", text: "failed" },
    cancelled: { icon: "⊘", color: "#999", text: "cancelled" },
};

const STYLE_ID = "extracting-node-animations";

function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
    .extract-loader {
      width: 14px;
      --b: 2px;
      aspect-ratio: 1;
      border-radius: 50%;
      padding: 1px;
      background: conic-gradient(#0000 10%, var(--loader-color)) content-box;
      -webkit-mask: repeating-conic-gradient(#0000 0deg, #000 1deg 20deg, #0000 21deg 36deg),
                    radial-gradient(farthest-side, #0000 calc(100% - var(--b) - 1px), #000 calc(100% - var(--b)));
      -webkit-mask-composite: destination-in;
      mask-composite: intersect;
      animation: extractLoaderSpin 1s infinite steps(10);
    }
    @keyframes extractLoaderSpin { to { transform: rotate(1turn) } }
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
    const startAnalyzeScript = useVideoStore((s) => s.startAnalyzeScript);
    const stopAnalyzeScript = useVideoStore((s) => s.stopAnalyzeScript);
    const startAnalyzeAudio = useVideoStore((s) => s.startAnalyzeAudio);
    const startAnalyzeVisual = useVideoStore((s) => s.startAnalyzeVisual);
    const visualStatus = useVideoStore((s) => s.visualStatus);
    const visualTime = useVideoStore((s) => s.visualTime);
    const stopAnalyzeVisual = useVideoStore((s) => s.stopAnalyzeVisual);
    const stopAnalyzeAudio = useVideoStore((s) => s.stopAnalyzeAudio);
    const audioStatus = useVideoStore((s) => s.audioStatus);
    const audioTime = useVideoStore((s) => s.audioTime);
    const { hasError } = useNodeError("extracting");

    injectStyles();

    const getStatus = (key: string) => {
        if (key === "script") return scriptStatus;
        if (key === "bgm") return audioStatus;
        if (key === "features") return visualStatus;
        return "idle";
    };

    const formatTime = (t: number | null) => {
        if (t == null) return "";
        return ` (${t.toFixed(2)}s)`;
    };

    const getTimeLabel = (key: string) => {
        if (key === "script") return formatTime(scriptTime);
        if (key === "bgm") return formatTime(audioTime);
        if (key === "features") return formatTime(visualTime);
        return "";
    };

    const allSettled =
        (scriptStatus === "success" ||
            scriptStatus === "error" ||
            scriptStatus === "cancelled") &&
        (audioStatus === "success" ||
            audioStatus === "error" ||
            audioStatus === "cancelled") &&
        (visualStatus === "success" ||
            visualStatus === "error" ||
            visualStatus === "cancelled");

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
                    <ActionButton
                        variant="primary"
                        label="▶ START EXTRACTING"
                        enabled={!!compressResult}
                        accent="#333"
                        onClick={() => {
                            startAnalyzeScript();
                            startAnalyzeAudio();
                            startAnalyzeVisual();
                        }}
                    />
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
                                STATUS_CONFIG[status] || STATUS_CONFIG.idle;
                            const timeLabel = getTimeLabel(item.key);

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
                                    {cfg.spin ? (
                                        <div
                                            className="extract-loader"
                                            style={{
                                                ["--loader-color" as any]:
                                                    cfg.color,
                                                marginRight: "8px",
                                            }}
                                        />
                                    ) : (
                                        <span
                                            style={{
                                                color: cfg.color,
                                                fontSize: "10px",
                                                marginRight: "8px",
                                                fontWeight: 700,
                                                display: "inline-flex",
                                                alignItems: "center",
                                                justifyContent: "center",
                                                width: "14px",
                                                height: "14px",
                                            }}
                                        >
                                            {cfg.icon}
                                        </span>
                                    )}
                                    <span
                                        style={{
                                            flex: 1,
                                            color:
                                                status === "success"
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

                        {allSettled ? (
                            <ActionButton
                                variant="muted"
                                label="↻ RESTART"
                                onClick={() => {
                                    startAnalyzeScript();
                                    startAnalyzeAudio();
                                    startAnalyzeVisual();
                                }}
                            />
                        ) : (
                            <ActionButton
                                variant="muted"
                                label="■ STOP"
                                onClick={() => {
                                    stopAnalyzeScript();
                                    stopAnalyzeAudio();
                                    stopAnalyzeVisual();
                                }}
                            />
                        )}
                    </div>
                )}
            </div>
        </BaseNode>
    );
}
