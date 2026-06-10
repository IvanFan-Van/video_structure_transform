import { useMemo } from "react";
import { BaseNode } from "../ui/BaseNode";
import { ActionButton } from "../ui/ActionButton";
import { StatusHeader } from "../ui/StatusHeader";
import { PreviewStill } from "../ui/PreviewStill";
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

const NODE_ID = "version_preview";
const ACCENT = "#8b5cf6";

export function VersionPreviewNode({ x, y, onPosChange }: Props) {
    const { hasError } = useNodeError(NODE_ID);

    const planResult = useVideoStore((s) => s.planResult);
    const selectedStyle = useVideoStore((s) => s.selectedStyle);
    const previewStatus = useVideoStore((s) => s.previewStatus);
    const previewResults = useVideoStore((s) => s.previewResults);
    const previewPhase = useVideoStore((s) => s.previewPhase);
    const previewStyleIndex = useVideoStore((s) => s.previewStyleIndex);
    const previewTotalStyles = useVideoStore((s) => s.previewTotalStyles);
    const startPreview = useVideoStore((s) => s.startPreview);
    const stopPreview = useVideoStore((s) => s.stopPreview);
    const setSelectedStyle = useVideoStore((s) => s.setSelectedStyle);
    const fetchStyles = useVideoStore((s) => s.fetchStyles);

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
    const isLoading = previewStatus === "loading";
    const hasResults = previewResults.length > 0;

    const handleStartPreview = () => {
        fetchStyles();
        startPreview();
    };

    return (
        <BaseNode
            x={x}
            y={y}
            w={320}
            title="Version Preview"
            active={enabled}
            accent={ACCENT}
            error={hasError}
            id={NODE_ID}
            onPosChange={onPosChange}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                }}
            >
                {/* ── Idle / No preview yet ── */}
                {previewStatus === "idle" && !hasResults && (
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "6px",
                            alignItems: "center",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "9px",
                                color: "#999",
                                textAlign: "center",
                            }}
                        >
                            Generate style previews to compare versions
                        </div>
                        <ActionButton
                            variant="primary"
                            label="Generate Previews"
                            enabled={enabled && !isLoading}
                            accent={ACCENT}
                            onClick={handleStartPreview}
                        />
                    </div>
                )}

                {/* ── Loading state ── */}
                {isLoading && (
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "6px",
                            alignItems: "center",
                        }}
                    >
                        <StatusHeader
                            variant="loading"
                            label="Generating previews..."
                        />
                        {previewPhase && (
                            <div
                                style={{
                                    fontSize: "8px",
                                    color: "#888",
                                    textAlign: "center",
                                }}
                            >
                                {previewPhase === "building"
                                    ? `Building style ${previewStyleIndex + 1}/${previewTotalStyles}...`
                                    : previewPhase === "rendering"
                                      ? `Rendering preview ${previewStyleIndex + 1}/${previewTotalStyles}...`
                                      : previewPhase}
                            </div>
                        )}
                        <ActionButton
                            variant="muted"
                            label="Stop"
                            enabled={true}
                            accent={ACCENT}
                            onClick={stopPreview}
                        />
                    </div>
                )}

                {/* ── Preview results grid ── */}
                {hasResults && previewStatus === "success" && (
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "8px",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "7px",
                                fontWeight: 600,
                                letterSpacing: "1px",
                                color: "#bbb",
                            }}
                        >
                            SELECT VERSION
                        </div>
                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: "6px",
                            }}
                        >
                            {previewResults.map((item) => {
                                const isSelected = selectedStyle === item.style;
                                return (
                                    <div
                                        key={item.style}
                                        onClick={() =>
                                            setSelectedStyle(item.style)
                                        }
                                        style={{
                                            cursor: "pointer",
                                            border: `2px solid ${
                                                isSelected ? ACCENT : "#e8e8e8"
                                            }`,
                                            borderRadius: "6px",
                                            padding: "4px",
                                            background: isSelected
                                                ? "#f5f3ff"
                                                : "#fff",
                                            transition: "border-color 0.15s",
                                        }}
                                    >
                                        <PreviewStill
                                            stillPath={item.still_path}
                                            alt={item.label}
                                            style={{
                                                width: "100%",
                                                height: "80px",
                                            }}
                                        />
                                        <div
                                            style={{
                                                fontSize: "8px",
                                                fontWeight: 700,
                                                color: isSelected
                                                    ? ACCENT
                                                    : "#333",
                                                marginTop: "3px",
                                                textAlign: "center",
                                            }}
                                        >
                                            {item.label}
                                        </div>
                                        <div
                                            style={{
                                                fontSize: "6px",
                                                color: "#999",
                                                textAlign: "center",
                                                lineHeight: "1.3",
                                            }}
                                        >
                                            {item.description}
                                        </div>
                                        <div
                                            style={{
                                                fontSize: "6px",
                                                color: "#bbb",
                                                textAlign: "center",
                                            }}
                                        >
                                            {item.scene_count} scenes /{" "}
                                            {(
                                                item.duration_frames / 30
                                            ).toFixed(1)}
                                            s
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        <ActionButton
                            variant="muted"
                            label="Regenerate Previews"
                            enabled={true}
                            accent={ACCENT}
                            onClick={handleStartPreview}
                            style={{ fontSize: "8px" }}
                        />
                    </div>
                )}

                {/* ── Error state ── */}
                {previewStatus === "error" && (
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "6px",
                            alignItems: "center",
                        }}
                    >
                        <StatusHeader variant="error" label="Preview failed" />
                        <ActionButton
                            variant="primary"
                            label="Retry Preview"
                            enabled={enabled}
                            accent={ACCENT}
                            onClick={handleStartPreview}
                        />
                    </div>
                )}
            </div>
        </BaseNode>
    );
}
