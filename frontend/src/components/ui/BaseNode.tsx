import React from "react";
import { useDraggable } from "../../hooks/useDraggable";
import { useCanvasStore } from "../../store/useCanvasStore";

interface BaseNodeProps {
    x: number;
    y: number;
    w: number;
    title: string;
    children: React.ReactNode;
    active: boolean;
    accent?: string;
    error?: boolean;
    id: string;
    tourId?: string;
    onPosChange: (
        id: string,
        x: number,
        y: number,
        w: number,
        h: number,
    ) => void;
}

export function BaseNode({
    x,
    y,
    w,
    title,
    children,
    active,
    accent,
    error,
    id,
    tourId,
    onPosChange,
}: BaseNodeProps) {
    const selectedIds = useCanvasStore((s) => s.selectedIds);
    const moveNodes = useCanvasStore((s) => s.moveNodes);
    const clearSelection = useCanvasStore((s) => s.clearSelection);

    const selected = selectedIds.includes(id);

    const onDragDelta = React.useCallback(
        (dx: number, dy: number) => {
            const others = selectedIds.filter((sid) => sid !== id);
            if (others.length > 0) moveNodes(others, dx, dy);
        },
        [selectedIds, moveNodes, id],
    );

    const { p, onMouseDown: rawMouseDown, ref } = useDraggable(x, y, id, onPosChange, onDragDelta);

    const onMouseDown = (e: React.MouseEvent) => {
        if (!selected && selectedIds.length > 0) {
            clearSelection();
        }
        rawMouseDown(e);
    };

    const effectiveColor = selected
        ? "#3b82f6"
        : error
          ? "#ef4444"
          : active
            ? accent || "#333"
            : "#e0e0e0";
    const hasGlow = selected || active || error;
    const glowColor = selected ? "#3b82f6" : error ? "#ef4444" : accent || "#333";
    const dividerColor = error
        ? "#fecaca"
        : selected
          ? "#bfdbfe"
          : active
            ? (accent || "#333") + "20"
            : "#f0f0f0";

    return (
        <div
            ref={ref}
            onMouseDown={onMouseDown}
            data-tour={tourId}
            style={{
                position: "absolute",
                left: p.x,
                top: p.y,
                width: w,
                background: "#fff",
                borderRadius: "3px",
                border: "1px solid " + effectiveColor,
                boxShadow: hasGlow
                    ? "0 2px 12px " + glowColor + "15"
                    : "0 1px 3px rgba(0,0,0,0.04)",
                cursor: "grab",
                userSelect: "none",
                zIndex: 10,
                transition: "border-color 0.3s, box-shadow 0.3s",
            }}
        >
            <div
                style={{
                    padding: "8px 12px",
                    borderBottom: "1px solid " + dividerColor,
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                }}
            >
                <span
                    style={{
                        fontSize: "10px",
                        fontWeight: 600,
                        letterSpacing: "1.5px",
                        color: active || error ? "#555" : "#bbb",
                        fontFamily: "JetBrains Mono, monospace",
                        textTransform: "uppercase",
                    }}
                >
                    {title}
                </span>
            </div>
            <div
                style={{
                    padding: "12px",
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "11px",
                }}
            >
                {children}
            </div>
        </div>
    );
}
