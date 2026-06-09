import { useState, useEffect } from "react";
import { FiExternalLink } from "react-icons/fi";
import { apiFetch } from "../../lib/api";

interface CoverImageProps {
    coverImageAssetId: string | null | undefined;
    videoAssetId: string | null | undefined;
    alt: string;
    maxHeight?: number;
}

export function CoverImage({
    coverImageAssetId,
    videoAssetId,
    alt,
    maxHeight = 120,
}: CoverImageProps) {
    const [url, setUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [hovered, setHovered] = useState(false);

    useEffect(() => {
        if (!coverImageAssetId) {
            setUrl(null);
            setLoading(false);
            return;
        }

        let cancelled = false;
        let objectUrl: string | null = null;
        setLoading(true);

        apiFetch(`/api/files/${coverImageAssetId}`)
            .then((res) => {
                if (!res.ok) throw new Error("fetch failed");
                return res.blob();
            })
            .then((blob) => {
                if (cancelled) return;
                objectUrl = URL.createObjectURL(blob);
                setUrl(objectUrl);
                setLoading(false);
            })
            .catch(() => {
                if (!cancelled) {
                    setUrl(null);
                    setLoading(false);
                }
            });

        return () => {
            cancelled = true;
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [coverImageAssetId]);

    useEffect(() => {
        return () => {
            if (url) URL.revokeObjectURL(url);
        };
    }, []);

    const handleOpenVideo = async () => {
        if (!videoAssetId) return;
        try {
            const res = await apiFetch(`/api/files/${videoAssetId}`);
            if (!res.ok) return;
            const blob = await res.blob();
            const videoUrl = URL.createObjectURL(blob);
            window.open(videoUrl, "_blank", "noopener,noreferrer");
        } catch {
            // silent fail
        }
    };

    if (!coverImageAssetId) return null;

    return (
        <div
            style={{
                position: "relative",
                borderRadius: "3px",
                overflow: "hidden",
                border: "1px solid #f0f0f0",
                maxHeight: `${maxHeight}px`,
            }}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            {loading || !url ? (
                <div
                    style={{
                        width: "100%",
                        height: `${maxHeight}px`,
                        background: "#f0f0f0",
                    }}
                />
            ) : (
                <img
                    src={url}
                    alt={alt}
                    style={{
                        width: "100%",
                        display: "block",
                        objectFit: "cover",
                        maxHeight: `${maxHeight}px`,
                    }}
                />
            )}

            {videoAssetId && url && (
                <div
                    onClick={handleOpenVideo}
                    title="Open original video"
                    style={{
                        position: "absolute",
                        top: 0,
                        right: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "28px",
                        height: "28px",
                        background: "rgba(0,0,0,0.45)",
                        borderRadius: "0 3px 0 6px",
                        opacity: hovered ? 1 : 0,
                        transition: "opacity 0.15s",
                        cursor: "pointer",
                        pointerEvents: hovered ? "auto" : "none",
                    }}
                >
                    <FiExternalLink size={13} color="#fff" />
                </div>
            )}
        </div>
    );
}
