import { useRef } from "react";
import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
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

export function ReferenceNode({ x, y, onPosChange }: Props) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const isUploading = useVideoStore((s) => s.isUploading);
    const uploadProgress = useVideoStore((s) => s.uploadProgress);
    const uploadResult = useVideoStore((s) => s.uploadResult);
    const uploadVideo = useVideoStore((s) => s.uploadVideo);
    const thumbnailUrl = useVideoStore((s) => s.thumbnailUrl);
    const videoErrors = useVideoStore((s) => s.videoErrors);
    const hasError = videoErrors.some((e) => e.nodeId === "reference");

    const handleFile = (file: File) => uploadVideo(file);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer?.files[0];
        if (file) handleFile(file);
    };

    return (
        <BaseNode
            x={x}
            y={y}
            w={280}
            title="Reference"
            active={!!uploadResult || isUploading}
            accent="#6366f1"
            error={hasError}
            id="reference"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp4,.mov,.avi,.mkv,.webm,.flv,.wmv"
                    style={{ display: "none" }}
                    onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleFile(f);
                    }}
                />
                <div
                    onDragOver={(e) => {
                        e.preventDefault();
                        e.currentTarget.style.borderColor = "#999";
                    }}
                    onDragLeave={(e) => {
                        e.currentTarget.style.borderColor = "#d4d4d4";
                    }}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    style={{
                        border: "1.5px dashed #d4d4d4",
                        borderRadius: "3px",
                        padding: "14px",
                        textAlign: "center",
                        color: "#bbb",
                        fontSize: "10px",
                        cursor: "pointer",
                    }}
                >
                    drop or click to upload video
                    <div
                        style={{
                            fontSize: "8px",
                            color: "#ddd",
                            marginTop: "3px",
                        }}
                    >
                        .mp4 .mov .avi .mkv .webm
                    </div>
                </div>
                {thumbnailUrl && (
                    <div
                        style={{
                            borderRadius: "3px",
                            overflow: "hidden",
                            maxHeight: "120px",
                            border: "1px solid #f0f0f0",
                            background: "#fafafa",
                        }}
                    >
                        <img
                            src={thumbnailUrl}
                            alt="video cover"
                            style={{
                                width: "100%",
                                display: "block",
                                objectFit: "cover",
                                maxHeight: "120px",
                            }}
                        />
                    </div>
                )}
                {isUploading && (
                    <>
                        <div
                            style={{
                                height: "2px",
                                background: "#f0f0f0",
                                borderRadius: "1px",
                                overflow: "hidden",
                            }}
                        >
                            <div
                                style={{
                                    height: "100%",
                                    width: uploadProgress + "%",
                                    background: "#6366f1",
                                    transition: "width 0.2s",
                                }}
                            />
                        </div>
                        <div
                            style={{
                                fontSize: "9px",
                                color: "#999",
                                textAlign: "center",
                            }}
                        >
                            {uploadProgress}%
                        </div>
                    </>
                )}
                {uploadResult && (
                    <div
                        style={{
                            fontSize: "10px",
                            color: "#888",
                            lineHeight: "16px",
                        }}
                    >
                        <div
                            style={{
                                color: "#22c55e",
                                fontWeight: 600,
                                fontSize: "10px",
                                marginBottom: "4px",
                            }}
                        >
                            ✓ Upload Complete
                        </div>
                        <div>
                            codec:{" "}
                            <span style={{ color: "#333", fontWeight: 600 }}>
                                {uploadResult.metadata.codec ?? "—"}
                            </span>
                        </div>
                        <div>
                            {uploadResult.metadata.width ?? "—"} ×{" "}
                            {uploadResult.metadata.height ?? "—"}
                        </div>
                        <div>
                            fps: {uploadResult.metadata.fps ?? "—"} duration:{" "}
                            {uploadResult.metadata.duration?.toFixed(1) ?? "—"}s
                        </div>
                        <div>
                            size:{" "}
                            <span style={{ color: "#333", fontWeight: 600 }}>
                                {fmtSize(uploadResult.metadata.size)}
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </BaseNode>
    );
}
