import { useVideoStore } from "../store/useVideoStore";

export function useNodeError(nodeId: string) {
    const videoErrors = useVideoStore((s) => s.videoErrors);
    const hasError = videoErrors.some((e) => e.nodeId === nodeId);
    return { hasError };
}
