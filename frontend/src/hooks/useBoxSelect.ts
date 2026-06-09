import { useState, useCallback, useEffect, useRef } from "react";
import { Pos } from "../store/types";

interface BoxSelectResult {
    isSelecting: boolean;
    rect: { x: number; y: number; w: number; h: number } | null;
    onMouseDown: (e: React.MouseEvent) => void;
}

export function useBoxSelect(
    zoom: number,
    panX: number,
    panY: number,
    positions: Record<string, Pos>,
    onComplete: (ids: string[]) => void,
): BoxSelectResult {
    const [isSelecting, setIsSelecting] = useState(false);
    const [rect, setRect] = useState<{
        x: number;
        y: number;
        w: number;
        h: number;
    } | null>(null);

    const selectingRef = useRef(false);
    const startRef = useRef({ sx: 0, sy: 0 });
    const lastRef = useRef({ sx: 0, sy: 0 });
    const cbRef = useRef(onComplete);
    cbRef.current = onComplete;
    const posRef = useRef(positions);
    posRef.current = positions;
    const zoomRef = useRef(zoom);
    zoomRef.current = zoom;
    const panRef = useRef({ x: panX, y: panY });
    panRef.current = { x: panX, y: panY };

    const onMouseDown = useCallback((e: React.MouseEvent) => {
        if (!e.ctrlKey) return;
        if ((e.target as HTMLElement).closest("[data-tour]")) {
            // Ctrl+click on a node — do NOT start box select
            return;
        }
        e.preventDefault();
        const p = { sx: e.clientX, sy: e.clientY };
        startRef.current = p;
        lastRef.current = p;
        setRect({ x: p.sx, y: p.sy, w: 0, h: 0 });
        setIsSelecting(true);
        selectingRef.current = true;
    }, []);

    useEffect(() => {
        const mv = (e: MouseEvent) => {
            if (!selectingRef.current) return;
            lastRef.current = { sx: e.clientX, sy: e.clientY };
            const sx = startRef.current.sx;
            const sy = startRef.current.sy;
            const cx = e.clientX;
            const cy = e.clientY;
            setRect({
                x: Math.min(sx, cx),
                y: Math.min(sy, cy),
                w: Math.abs(cx - sx),
                h: Math.abs(cy - sy),
            });
        };
        const up = () => {
            if (!selectingRef.current) return;
            selectingRef.current = false;
            setIsSelecting(false);
            setRect(null);

            const { sx, sy } = startRef.current;
            const ex = lastRef.current.sx;
            const ey = lastRef.current.sy;
            const z = zoomRef.current;
            const { x: px, y: py } = panRef.current;

            const screenMinX = Math.min(sx, ex);
            const screenMinY = Math.min(sy, ey);
            const screenMaxX = Math.max(sx, ex);
            const screenMaxY = Math.max(sy, ey);

            const lMinX = (screenMinX - px) / z;
            const lMinY = (screenMinY - py) / z;
            const lMaxX = (screenMaxX - px) / z;
            const lMaxY = (screenMaxY - py) / z;

            const ids: string[] = [];
            for (const [id, p] of Object.entries(posRef.current)) {
                if (
                    p.x + p.w > lMinX &&
                    p.x < lMaxX &&
                    p.y + p.h > lMinY &&
                    p.y < lMaxY
                ) {
                    ids.push(id);
                }
            }
            cbRef.current(ids);
        };
        window.addEventListener("mousemove", mv);
        window.addEventListener("mouseup", up);
        return () => {
            window.removeEventListener("mousemove", mv);
            window.removeEventListener("mouseup", up);
        };
    }, []);

    return { isSelecting, rect, onMouseDown };
}
