import { useRef, useCallback, useEffect } from "react";
import { useCanvasStore } from "../store/useCanvasStore";

export function usePan(zoom: number) {
    const panX = useCanvasStore((s) => s.panX);
    const panY = useCanvasStore((s) => s.panY);
    const setPan = useCanvasStore((s) => s.setPan);

    const dragging = useRef(false);
    const last = useRef({ x: 0, y: 0 });

    const onMouseDown = useCallback((e: React.MouseEvent) => {
        if (
            ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(
                (e.target as HTMLElement).tagName,
            )
        )
            return;
        dragging.current = true;
        last.current = { x: e.clientX, y: e.clientY };
        e.preventDefault();
    }, []);

    useEffect(() => {
        const mv = (e: MouseEvent) => {
            if (!dragging.current) return;
            const dx = e.clientX - last.current.x;
            const dy = e.clientY - last.current.y;
            last.current = { x: e.clientX, y: e.clientY };
            setPan((prev) => ({
                x: prev.x + dx,
                y: prev.y + dy,
            }));
        };
        const up = () => {
            dragging.current = false;
        };
        window.addEventListener("mousemove", mv);
        window.addEventListener("mouseup", up);
        return () => {
            window.removeEventListener("mousemove", mv);
            window.removeEventListener("mouseup", up);
        };
    }, [zoom, setPan]);

    return { panX, panY, onMouseDown };
}
