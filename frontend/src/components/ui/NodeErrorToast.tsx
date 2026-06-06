import { useState } from "react";
import { useVideoStore } from "../../store/useVideoStore";

export function NodeErrorToast() {
    const errors = useVideoStore((s) => s.videoErrors);
    const dismissError = useVideoStore((s) => s.dismissError);
    const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

    const toggleExpand = (id: number) => {
        setExpandedIds((prev) => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    if (errors.length === 0) return null;

    return (
        <div
            style={{
                position: "fixed",
                bottom: 16,
                right: 20,
                zIndex: 200,
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                width: "360px",
                maxWidth: "calc(100vw - 40px)",
            }}
        >
            {errors.map((err) => {
                const expanded = expandedIds.has(err.id);
                return (
                    <div
                        key={err.id}
                        style={{
                            background: "#fff",
                            border: "1px solid #fecaca",
                            borderRadius: "6px",
                            boxShadow: "0 2px 12px rgba(239,68,68,0.10)",
                            overflow: "hidden",
                            width: "100%",
                            fontFamily: "'JetBrains Mono', monospace",
                        }}
                    >
                        <div
                            onClick={() => toggleExpand(err.id)}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                padding: "8px 12px",
                                cursor: "pointer",
                                userSelect: "none",
                                background: "#fef2f2",
                            }}
                        >
                            <span
                                style={{
                                    fontSize: "9px",
                                    color: "#ef4444",
                                    letterSpacing: "1px",
                                    fontWeight: 600,
                                    textTransform: "uppercase",
                                    marginRight: "8px",
                                }}
                            >
                                {err.nodeId}
                            </span>
                            <span
                                style={{
                                    fontSize: "10px",
                                    color: "#991b1b",
                                    flex: 1,
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                    whiteSpace: "nowrap",
                                    textTransform: "uppercase",
                                }}
                            >
                                {err.message}
                            </span>
                            <span
                                style={{
                                    fontSize: "8px",
                                    color: "#fca5a5",
                                    marginLeft: "6px",
                                }}
                            >
                                {expanded ? "▲" : "▼"}
                            </span>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    dismissError(err.id);
                                }}
                                style={{
                                    marginLeft: "8px",
                                    background: "transparent",
                                    border: "none",
                                    color: "#fca5a5",
                                    fontSize: "14px",
                                    cursor: "pointer",
                                    padding: "0 2px",
                                    lineHeight: 1,
                                    fontFamily: "inherit",
                                }}
                            >
                                ✕
                            </button>
                        </div>
                        {expanded && (
                            <div
                                style={{
                                    padding: "8px 12px",
                                    borderTop: "1px solid #fecaca",
                                }}
                            >
                                <div
                                    style={{
                                        fontSize: "8px",
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                        marginBottom: "2px",
                                        overflowWrap: "break-word",
                                    }}
                                >
                                    CODE: {err.code}
                                </div>
                                <div
                                    style={{
                                        fontSize: "10px",
                                        color: "#666",
                                        lineHeight: "16px",
                                        wordBreak: "break-all",
                                    }}
                                >
                                    {err.details}
                                </div>
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
