import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
import { useNodeError } from "../../hooks/useNodeError";
import { ActionButton } from "../ui/ActionButton";
import { CoverImage } from "../ui/CoverImage";
import { StatusHeader } from "../ui/StatusHeader";
import { Tooltip } from "../ui/Tooltip";
import { fmtSize } from "../../utils";

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

function CompareRow({
    label,
    before,
    after,
}: {
    label: string;
    before: string;
    after: string;
}) {
    return (
        <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: "#bbb" }}>{label}</span>
            <span>
                <span style={{ color: "#999" }}>{before}</span> →{" "}
                <span style={{ color: "#333", fontWeight: 600 }}>{after}</span>
            </span>
        </div>
    );
}

export function CompressNode({ x, y, onPosChange }: Props) {
    const uploadResult = useVideoStore((s) => s.uploadResult);
    const isCompressing = useVideoStore((s) => s.isCompressing);
    const compressResult = useVideoStore((s) => s.compressResult);
    const startCompress = useVideoStore((s) => s.startCompress);
    const stopCompress = useVideoStore((s) => s.stopCompress);
    const { hasError } = useNodeError("compress");

    const savingsPct =
        compressResult && uploadResult
            ? Math.round(
                  (1 -
                      (compressResult.metadata.size ?? 0) /
                          (uploadResult.metadata.size ?? 1)) *
                      100,
              )
            : null;

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Compress"
            active={!!uploadResult || !!compressResult}
            accent="#06b6d4"
            error={hasError}
            id="compress"
            tourId="compress"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
                {!isCompressing && !compressResult && (
                    <Tooltip tip="使用 Compress Config 中的参数压缩视频，减小文件体积便于后续处理">
                    <ActionButton
                        variant="primary"
                        label="▶ COMPRESS"
                        enabled={!!uploadResult}
                        accent="#06b6d4"
                        onClick={startCompress}
                    />
                    </Tooltip>
                )}
                {isCompressing && (
                    <>
                        <StatusHeader
                            variant="loading"
                            label="Compressing"
                            accent="#06b6d4"
                        />
                        <ActionButton
                            variant="muted"
                            label="■ STOP"
                            onClick={stopCompress}
                        />
                    </>
                )}
                {compressResult && (
                    <>
                        <StatusHeader
                            variant="success"
                            label="COMPRESSED"
                            accent="#06b6d4"
                        />
                        <CoverImage
                            coverImageAssetId={
                                compressResult.cover_image_asset_id
                            }
                            videoAssetId={compressResult.asset_id}
                            alt="Compressed video cover"
                        />
                        {uploadResult && (
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
                                        marginBottom: "2px",
                                        color: "#bbb",
                                        fontSize: "8px",
                                        letterSpacing: "1px",
                                    }}
                                >
                                    <span>Before → After</span>
                                </div>
                                <CompareRow
                                    label="resolution"
                                    before={`${uploadResult.metadata.width}×${uploadResult.metadata.height}`}
                                    after={`${compressResult.metadata.width}×${compressResult.metadata.height}`}
                                />
                                <CompareRow
                                    label="size"
                                    before={fmtSize(uploadResult.metadata.size)}
                                    after={fmtSize(
                                        compressResult.metadata.size,
                                    )}
                                />
                                <CompareRow
                                    label="fps"
                                    before={String(
                                        uploadResult.metadata.fps ?? "—",
                                    )}
                                    after={String(
                                        compressResult.metadata.fps ?? "—",
                                    )}
                                />
                                <CompareRow
                                    label="codec"
                                    before={uploadResult.metadata.codec ?? "—"}
                                    after={compressResult.metadata.codec ?? "—"}
                                />
                                {savingsPct !== null && (
                                    <div
                                        style={{
                                            textAlign: "center",
                                            marginTop: "4px",
                                            fontWeight: 600,
                                            fontSize: "10px",
                                            color:
                                                savingsPct > 0
                                                    ? "#22c55e"
                                                    : "#999",
                                        }}
                                    >
                                        {savingsPct > 0
                                            ? `${savingsPct}% smaller`
                                            : "same size"}
                                    </div>
                                )}
                            </div>
                        )}
                        <ActionButton
                            variant="muted"
                            label="RECOMPRESS"
                            onClick={startCompress}
                        />
                    </>
                )}
            </div>
        </BaseNode>
    );
}
