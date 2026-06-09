import { useState, useRef, useCallback, useEffect, useContext } from "react";
import { ZoomContext } from "../context/ZoomContext";
import { useCanvasStore } from "../store/useCanvasStore";

export function useDraggable(
    ix: number,
    iy: number,
    id: string,
    onPos: (id: string, x: number, y: number, w: number, h: number) => void,
    onDragDelta?: (dx: number, dy: number) => void,
) {
    const zoom = useContext(ZoomContext);

    const savedPos = useCanvasStore.getState().positions[id];
    const [p, setP] = useState(() =>
        savedPos ? { x: savedPos.x, y: savedPos.y } : { x: ix, y: iy },
    );

    const drag = useRef(false);
    const off = useRef({ x: 0, y: 0 });
    const ref = useRef<HTMLDivElement>(null);
    const prevP = useRef({ x: 0, y: 0 });
    const deltaCb = useRef(onDragDelta);
    deltaCb.current = onDragDelta;

    // Subscribe to store position for multi-drag sync
    const storePos = useCanvasStore((s) => s.positions[id]);
    useEffect(() => {
        if (drag.current) return;
        if (storePos) setP({ x: storePos.x, y: storePos.y });
    }, [storePos?.x, storePos?.y]);

    const onMouseDown = useCallback(
        (e: React.MouseEvent) => {
            if (
                ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(
                    (e.target as HTMLElement).tagName,
                )
            )
                return;
            e.stopPropagation();
            drag.current = true;
            prevP.current = { x: p.x, y: p.y };
            off.current = {
                x: e.clientX - p.x * zoom,
                y: e.clientY - p.y * zoom,
            };
            e.preventDefault();
        },
        [p, zoom],
    );

    useEffect(() => {
        const mv = (e: MouseEvent) => {
            if (drag.current) {
                const nx = (e.clientX - off.current.x) / zoom;
                const ny = (e.clientY - off.current.y) / zoom;
                if (deltaCb.current) {
                    deltaCb.current(
                        nx - prevP.current.x,
                        ny - prevP.current.y,
                    );
                }
                prevP.current = { x: nx, y: ny };
                setP({ x: nx, y: ny });
            }
        };
        const up = () => {
            drag.current = false;
        };
        window.addEventListener("mousemove", mv);
        window.addEventListener("mouseup", up);
        return () => {
            window.removeEventListener("mousemove", mv);
            window.removeEventListener("mouseup", up);
        };
    }, [zoom]);

    useEffect(() => {
        if (ref.current) {
            const r = ref.current.getBoundingClientRect();
            onPos(id, p.x, p.y, r.width / zoom, r.height / zoom);
        }
    }, [p, id, onPos, zoom]);

    return { p, onMouseDown, ref };
}
