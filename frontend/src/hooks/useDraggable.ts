import { useState, useRef, useCallback, useEffect, useContext } from "react";
import { ZoomContext } from "../context/ZoomContext";
import { useCanvasStore } from "../store/useCanvasStore";

export function useDraggable(
    ix: number,
    iy: number,
    id: string,
    onPos: (id: string, x: number, y: number, w: number, h: number) => void,
) {
    const zoom = useContext(ZoomContext);

    // 优先用 store 里的持久化坐标，没有则用传入的初始值
    const savedPos = useCanvasStore.getState().positions[id];
    const [p, setP] = useState(() =>
        savedPos ? { x: savedPos.x, y: savedPos.y } : { x: ix, y: iy },
    );

    const drag = useRef(false);
    const off = useRef({ x: 0, y: 0 });
    const ref = useRef<HTMLDivElement>(null);

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
                setP({
                    x: (e.clientX - off.current.x) / zoom,
                    y: (e.clientY - off.current.y) / zoom,
                });
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
