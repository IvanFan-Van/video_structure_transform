import { useCanvasStore } from "../store/useCanvasStore";

export function useNodePositions() {
    const positions = useCanvasStore((s) => s.positions);
    const updatePosition = useCanvasStore((s) => s.updatePosition);
    return { positions, update: updatePosition };
}
