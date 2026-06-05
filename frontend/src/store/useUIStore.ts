import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { Pos } from "./types";

interface UIState {
    zoom: number;
    panX: number;
    panY: number;
    nodePositions: Record<string, Pos>;
    positionTick: number;
}

interface UIActions {
    setZoom: (z: number) => void;
    addPanDelta: (dx: number, dy: number) => void;
    updateNodePosition: (
        id: string,
        x: number,
        y: number,
        w: number,
        h: number,
    ) => void;
    resetNodePositions: () => void;
}

export const useUIStore = create<UIState & UIActions>()(
    persist(
        (set) => ({
            zoom: 1,
            panX: 0,
            panY: 0,
            nodePositions: {},
            positionTick: 0,

            setZoom: (z) => set({ zoom: Math.max(0.2, Math.min(2, z)) }),
            addPanDelta: (dx, dy) =>
                set((s) => ({
                    panX: s.panX + dx / s.zoom,
                    panY: s.panY + dy / s.zoom,
                })),
            updateNodePosition: (id, x, y, w, h) =>
                set((s) => ({
                    nodePositions: {
                        ...s.nodePositions,
                        [id]: { x, y, w, h },
                    },
                    positionTick: s.positionTick + 1,
                })),
            resetNodePositions: () =>
                set((s) => ({
                    nodePositions: {},
                    positionTick: s.positionTick + 1,
                })),
        }),
        {
            name: "ui-store",
            storage: createJSONStorage(() => sessionStorage),
            partialize: (state) => ({
                zoom: state.zoom,
                panX: state.panX,
                panY: state.panY,
                nodePositions: state.nodePositions,
                positionTick: state.positionTick,
            }),
        },
    ),
);
