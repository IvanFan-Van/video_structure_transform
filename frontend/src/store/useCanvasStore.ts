import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { Pos } from "./types";

interface CanvasState {
    zoom: number;
    panX: number;
    panY: number;
    positions: Record<string, Pos>;

    setZoom: (updater: (prev: number) => number) => void;
    setPan: (
        updater: (prev: { x: number; y: number }) => { x: number; y: number },
    ) => void;
    updatePosition: (
        id: string,
        x: number,
        y: number,
        w: number,
        h: number,
    ) => void;
}

export const useCanvasStore = create<CanvasState>()(
    persist(
        (set) => ({
            zoom: 1,
            panX: 0,
            panY: 0,
            positions: {},

            setZoom: (updater) =>
                set((s) => ({
                    zoom: Math.min(2, Math.max(0.2, updater(s.zoom))),
                })),

            setPan: (updater) =>
                set((s) => {
                    const { x, y } = updater({ x: s.panX, y: s.panY });
                    return { panX: x, panY: y };
                }),

            updatePosition: (id, x, y, w, h) =>
                set((s) => ({
                    positions: { ...s.positions, [id]: { x, y, w, h } },
                })),
        }),
        {
            name: "canvas-state", // sessionStorage key
            storage: createJSONStorage(() => sessionStorage),
            // 只持久化纯数据，actions 不需要序列化
            partialize: (s) => ({
                zoom: s.zoom,
                panX: s.panX,
                panY: s.panY,
                positions: s.positions,
            }),
        },
    ),
);
