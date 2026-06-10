import { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { apiAxios } from "../../lib/api";

interface EffectInfo {
    name: string;
    category: string;
    description: string;
    demo_path: string | null;
    doc_path: string | null;
}

interface Props {
    open: boolean;
    onClose: () => void;
    onSelect: (name: string) => void;
    triggerRef: React.RefObject<HTMLElement | null>;
}

export function EffectSearch({ open, onClose, onSelect, triggerRef }: Props) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<EffectInfo[]>([]);
    const [allEffects, setAllEffects] = useState<EffectInfo[]>([]);
    const [loading, setLoading] = useState(false);
    const [pos, setPos] = useState({ x: 0, y: 0 });
    const [dragging, setDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const inputRef = useRef<HTMLInputElement>(null);
    const popupRef = useRef<HTMLDivElement>(null);
    const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [tooltip, setTooltip] = useState<{
        text: string;
        x: number;
        y: number;
        demoUrl: string | null;
    } | null>(null);

    useEffect(() => {
        if (!open) {
            if (hoverTimer.current) clearTimeout(hoverTimer.current);
            setTooltip(null);
            return;
        }
        const btn = triggerRef.current;
        if (!btn) return;
        const r = btn.getBoundingClientRect();
        setPos({ x: r.left + 8, y: r.bottom + 4 });

        setQuery("");
        setTimeout(() => inputRef.current?.focus(), 0);

        setLoading(true);
        apiAxios
            .get("/api/effects")
            .then((res) => {
                if (res.data.status === "success") {
                    const list = ((res.data.data ?? []) as EffectInfo[]).sort(
                        (a, b) => a.name.localeCompare(b.name),
                    );
                    setAllEffects(list);
                    setResults(list);
                }
            })
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [open]);

    useEffect(() => {
        if (!query.trim()) {
            setResults(allEffects);
            return;
        }
        const q = query.toLowerCase();
        setResults(
            allEffects.filter(
                (e) =>
                    e.name.toLowerCase().includes(q) ||
                    e.category.toLowerCase().includes(q),
            ),
        );
    }, [query, allEffects]);

    // Click outside to close
    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (
                popupRef.current &&
                !popupRef.current.contains(e.target as Node) &&
                triggerRef.current &&
                !triggerRef.current.contains(e.target as Node)
            ) {
                onClose();
            }
        };
        // Delay to avoid the click that opened the popup
        const t = setTimeout(
            () => window.addEventListener("mousedown", handler),
            0,
        );
        return () => {
            clearTimeout(t);
            window.removeEventListener("mousedown", handler);
        };
    }, [open, onClose]);

    // Drag logic
    const onDragStart = useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            setDragging(true);
            dragOffset.current = {
                x: e.clientX - pos.x,
                y: e.clientY - pos.y,
            };
        },
        [pos],
    );

    useEffect(() => {
        if (!dragging) return;
        const mv = (e: MouseEvent) => {
            setPos({
                x: e.clientX - dragOffset.current.x,
                y: e.clientY - dragOffset.current.y,
            });
        };
        const up = () => setDragging(false);
        window.addEventListener("mousemove", mv);
        window.addEventListener("mouseup", up);
        return () => {
            window.removeEventListener("mousemove", mv);
            window.removeEventListener("mouseup", up);
        };
    }, [dragging]);

    if (!open) return null;

    return createPortal(
        <div
            ref={popupRef}
            style={{
                position: "fixed",
                left: pos.x,
                top: pos.y,
                width: 260,
                maxHeight: 300,
                zIndex: 10000,
                background: "#fff",
                borderRadius: "6px",
                boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
                border: "1px solid #e8e8e8",
                display: "flex",
                flexDirection: "column",
                userSelect: dragging ? "none" : "auto",
            }}
        >
            {/* Drag handle */}
            <div
                onMouseDown={onDragStart}
                style={{
                    padding: "8px 10px 6px",
                    borderBottom: "1px solid #f0f0f0",
                    cursor: "grab",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                }}
            >
                <span style={{ fontSize: "8px", color: "#ccc" }}>⠿</span>
                <input
                    ref={inputRef}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search effects..."
                    onMouseDown={(e) => e.stopPropagation()}
                    style={{
                        flex: 1,
                        padding: "4px 6px",
                        fontSize: "10px",
                        fontFamily: "inherit",
                        border: "1px solid #e0e0e0",
                        borderRadius: "3px",
                        outline: "none",
                        boxSizing: "border-box",
                    }}
                    onFocus={(e) =>
                        (e.currentTarget.style.borderColor = "#f97316")
                    }
                    onBlur={(e) =>
                        (e.currentTarget.style.borderColor = "#e0e0e0")
                    }
                />
                <button
                    onClick={onClose}
                    onMouseDown={(e) => e.stopPropagation()}
                    style={{
                        fontSize: "10px",
                        color: "#bbb",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: "0 2px",
                        fontFamily: "inherit",
                    }}
                >
                    ×
                </button>
            </div>

            {/* Results list */}
            <div
                style={{
                    flex: 1,
                    overflowY: "auto",
                    padding: "4px 0",
                    fontSize: "10px",
                }}
            >
                {loading ? (
                    <div
                        style={{
                            padding: "10px",
                            color: "#bbb",
                            textAlign: "center",
                            fontSize: "9px",
                        }}
                    >
                        Loading...
                    </div>
                ) : results.length === 0 ? (
                    <div
                        style={{
                            padding: "10px",
                            color: "#bbb",
                            textAlign: "center",
                            fontSize: "9px",
                        }}
                    >
                        No effects found
                    </div>
                ) : (
                    results.map((ef) => (
                        <button
                            key={ef.name}
                            onClick={() => onSelect(ef.name)}
                            style={{
                                width: "100%",
                                textAlign: "left",
                                padding: "5px 10px",
                                border: "none",
                                background: "transparent",
                                cursor: "pointer",
                                fontFamily: "inherit",
                            }}
                            onMouseEnter={(e) => {
                                (e.currentTarget.style.background = "#fff7ed");
                                const r =
                                    e.currentTarget.getBoundingClientRect();
                                hoverTimer.current = setTimeout(() => {
                                    setTooltip({
                                        text: ef.description,
                                        x: r.right + 8,
                                        y: r.top,
                                        demoUrl: ef.demo_path
                                            ? `/api${ef.demo_path}`
                                            : null,
                                    });
                                }, 600);
                            }}
                            onMouseLeave={(e) => {
                                (e.currentTarget.style.background =
                                    "transparent");
                                if (hoverTimer.current) {
                                    clearTimeout(hoverTimer.current);
                                    hoverTimer.current = null;
                                }
                                setTooltip(null);
                            }}
                        >
                            <div
                                style={{
                                    fontWeight: 600,
                                    color: "#333",
                                    fontSize: "9px",
                                }}
                            >
                                {ef.name}
                            </div>
                            <div
                                style={{
                                    fontSize: "7px",
                                    color: "#bbb",
                                    marginTop: "1px",
                                }}
                            >
                                {ef.category}
                            </div>
                            <div
                                style={{
                                    fontSize: "7px",
                                    color: "#888",
                                    marginTop: "2px",
                                    lineHeight: "1.3",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                    whiteSpace: "nowrap",
                                }}
                            >
                                {ef.description}
                            </div>
                        </button>
                    ))
                )}
            </div>
            {tooltip && (
                <div
                    style={{
                        position: "fixed",
                        left: tooltip.x,
                        top: tooltip.y,
                        padding: "6px 10px",
                        background: "#333",
                        color: "#f5f5f5",
                        fontSize: "9px",
                        fontFamily: "'JetBrains Mono', monospace",
                        lineHeight: "1.5",
                        borderRadius: "4px",
                        whiteSpace: "pre-wrap",
                        maxWidth: "240px",
                        zIndex: 10001,
                        pointerEvents: "none",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.18)",
                    }}
                >
                    {tooltip.text}
                    {tooltip.demoUrl ? (
                        <video
                            src={tooltip.demoUrl}
                            autoPlay
                            loop
                            muted
                            playsInline
                            style={{
                                width: 200,
                                marginTop: 6,
                                borderRadius: 4,
                                display: "block",
                            }}
                        />
                    ) : (
                        <div
                            style={{
                                fontSize: "8px",
                                color: "#888",
                                marginTop: 4,
                            }}
                        >
                            (No demo available)
                        </div>
                    )}
                </div>
            )}
        </div>,
        document.body,
    );
}
