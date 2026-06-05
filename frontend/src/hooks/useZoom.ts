import { useEffect } from "react";
import { useCanvasStore } from "../store/useCanvasStore";

export function useZoom() {
    const zoom = useCanvasStore((s) => s.zoom);
    const setZoom = useCanvasStore((s) => s.setZoom);

    useEffect(() => {
        const onWheel = (e: WheelEvent) => {
            if (!e.ctrlKey && !e.metaKey) return;
            e.preventDefault();
            setZoom((z) => z - e.deltaY * 0.001);
        };
        window.addEventListener("wheel", onWheel, { passive: false });
        return () => window.removeEventListener("wheel", onWheel);
    }, [setZoom]);

    return zoom;
}
