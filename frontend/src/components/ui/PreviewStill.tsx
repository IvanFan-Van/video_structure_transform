import { useState, useEffect } from "react";
import { apiAxios } from "../../lib/api";

interface PreviewStillProps {
    stillPath: string;
    alt: string;
    style?: React.CSSProperties;
}

export function PreviewStill({ stillPath, alt, style }: PreviewStillProps) {
    const [url, setUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        let cancelled = false;
        let objectUrl: string | null = null;
        setLoading(true);

        apiAxios
            .get(`/api/render/still/${encodePath(stillPath)}`, {
                responseType: "blob",
            })
            .then((res) => {
                if (cancelled) return;
                objectUrl = URL.createObjectURL(res.data);
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
    }, [stillPath]);

    return (
        <div
            style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "#1a1a1a",
                borderRadius: "3px",
                overflow: "hidden",
                ...style,
            }}
        >
            {loading && (
                <div
                    style={{
                        fontSize: "7px",
                        color: "#666",
                    }}
                >
                    ...
                </div>
            )}
            {url && (
                <img
                    src={url}
                    alt={alt}
                    style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                    }}
                />
            )}
        </div>
    );
}

function encodePath(filePath: string): string {
    const parts = filePath.replace(/\\/g, "/").split("/");
    const previewIdx = parts.indexOf("preview");
    if (previewIdx === -1) return "";
    const relative = parts.slice(previewIdx + 1);
    return relative.join("/");
}
