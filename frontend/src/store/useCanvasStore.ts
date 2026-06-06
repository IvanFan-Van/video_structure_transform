import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { Pos } from "./types";

const DEFAULT_ZOOM = 0.5;
const DEFAULT_PAN_X = 0;
const DEFAULT_PAN_Y = 0;
const DEFAULT_POSITIONS: Record<string, Pos> = {
    reference: { x: 77, y: 295, w: 280, h: 113 },
    compress_config: { x: 553, y: 128, w: 300, h: 269.5 },
    compress: { x: 1116, y: 113, w: 300, h: 91.5 },
    extracting: { x: 503, y: 630, w: 300, h: 91.5 },
    script_analysis: { x: 1201, y: 315, w: 300, h: 91.5 },
    audio_analysis: { x: 1233, y: 560, w: 300, h: 91.5 },
    visual_analysis: { x: 1280, y: 787, w: 300, h: 91.5 },
};

const PRESET_KEY = "canvas-preset";

const loadPreset = () => {
    try {
        const raw = localStorage.getItem(PRESET_KEY);
        if (raw) {
            const p = JSON.parse(raw);
            if (
                typeof p.zoom === "number" &&
                typeof p.panX === "number" &&
                typeof p.panY === "number" &&
                p.positions &&
                typeof p.positions === "object"
            ) {
                return {
                    zoom: p.zoom,
                    panX: p.panX,
                    panY: p.panY,
                    positions: p.positions,
                };
            }
        }
    } catch {}
    return null;
};

const preset = loadPreset();

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
    savePreset: () => void;
}

export const useCanvasStore = create<CanvasState>()(
    persist(
        (set, get) => ({
            zoom: preset?.zoom ?? DEFAULT_ZOOM,
            panX: preset?.panX ?? DEFAULT_PAN_X,
            panY: preset?.panY ?? DEFAULT_PAN_Y,
            positions: preset?.positions ?? DEFAULT_POSITIONS,

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

            savePreset: () => {
                const { zoom, panX, panY, positions } = get();
                try {
                    localStorage.setItem(
                        PRESET_KEY,
                        JSON.stringify({ zoom, panX, panY, positions }),
                    );
                } catch {}
            },
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
