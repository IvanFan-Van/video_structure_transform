import { create } from "zustand";
import axios from "axios";
import {
    UploadResult,
    CompressResult,
    CompressConfig,
    NodeError,
} from "./types";
import { useAuthStore } from "./useAuthStore";

interface VideoState {
    isUploading: boolean;
    uploadProgress: number;
    uploadResult: UploadResult | null;
    thumbnailUrl: string | null;

    compressConfig: CompressConfig;

    isCompressing: boolean;
    compressResult: CompressResult | null;

    videoErrors: NodeError[];
}

interface VideoActions {
    uploadVideo: (file: File) => Promise<void>;
    setCompressConfig: (
        updater: CompressConfig | ((c: CompressConfig) => CompressConfig),
    ) => void;
    startCompress: () => Promise<void>;
    dismissError: (id: number) => void;
}

const initialCompressConfig: CompressConfig = {
    vcodec: "libx264",
    crf: 32,
    target_v_bitrate: null,
    scale_width: null,
    max_fps: 30,
    acodec: "aac",
    target_a_bitrate: "96k",
};

function makeError(
    nodeId: string,
    message: string,
    code: string,
    details: string,
): NodeError {
    return { id: Date.now(), nodeId, message, code, details };
}

function generateThumbnail(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(file);
        const video = document.createElement("video");
        video.preload = "metadata";
        video.muted = true;
        video.playsInline = true;
        video.src = url;
        // 当加载完视频时跳转到第一秒
        video.onloadeddata = () => {
            video.currentTime = 1;
        };
        // 当跳转完成后，绘制缩略图
        video.onseeked = () => {
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext("2d")!.drawImage(video, 0, 0);
            resolve(canvas.toDataURL("image/jpeg", 0.7));
            URL.revokeObjectURL(url);
        };
        video.onerror = () => {
            URL.revokeObjectURL(url);
            reject();
        };
    });
}

export const useVideoStore = create<VideoState & VideoActions>((set, get) => ({
    isUploading: false,
    uploadProgress: 0,
    uploadResult: null,
    thumbnailUrl: null,

    compressConfig: { ...initialCompressConfig },

    isCompressing: false,
    compressResult: null,

    videoErrors: [],

    uploadVideo: async (file) => {
        const token = useAuthStore.getState().token;
        set({ isUploading: true, uploadProgress: 0, uploadResult: null, compressResult: null });

        generateThumbnail(file).then((url) => set({ thumbnailUrl: url }));

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await axios.post("/api/upload", formData, {
                headers: { Authorization: `Bearer ${token}` },
                onUploadProgress: (e) => {
                    if (e.total) {
                        set({
                            uploadProgress: Math.round(
                                (e.loaded / e.total) * 100,
                            ),
                        });
                    }
                },
            });
            if (res.data.success) {
                set((s) => ({
                    uploadResult: res.data.data,
                    isUploading: false,
                    uploadProgress: 100,
                    videoErrors: s.videoErrors.filter(
                        (e) => e.nodeId !== "reference",
                    ),
                }));
            } else {
                const err = res.data.error || {
                    code: "UNKNOWN",
                    details: res.data.message,
                };
                set((s) => ({
                    isUploading: false,
                    videoErrors: [
                        ...s.videoErrors.filter(
                            (e) => e.nodeId !== "reference",
                        ),
                        makeError(
                            "reference",
                            res.data.message,
                            err.code,
                            err.details,
                        ),
                    ],
                }));
            }
        } catch {
            set((s) => ({
                isUploading: false,
                videoErrors: [
                    ...s.videoErrors.filter((e) => e.nodeId !== "reference"),
                    makeError(
                        "reference",
                        "Network error",
                        "NETWORK_ERROR",
                        "Unable to reach the server. Check your connection and try again.",
                    ),
                ],
            }));
        }
    },

    setCompressConfig: (updater) => {
        set((s) => ({
            compressConfig:
                typeof updater === "function"
                    ? updater(s.compressConfig)
                    : updater,
        }));
    },

    startCompress: async () => {
        const { uploadResult, compressConfig } = get();
        if (!uploadResult) return;
        const token = useAuthStore.getState().token;
        set({ isCompressing: true, compressResult: null });

        try {
            const res = await axios.post(
                "/api/compress",
                {
                    asset_id: uploadResult.asset_id,
                    vcodec: compressConfig.vcodec,
                    crf: compressConfig.crf,
                    target_v_bitrate: compressConfig.target_v_bitrate,
                    scale_width: compressConfig.scale_width,
                    max_fps: compressConfig.max_fps,
                    acodec: compressConfig.acodec,
                    target_a_bitrate: compressConfig.target_a_bitrate,
                },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );
            if (res.data.success) {
                set((s) => ({
                    compressResult: res.data.data,
                    isCompressing: false,
                    videoErrors: s.videoErrors.filter(
                        (e) => e.nodeId !== "compress",
                    ),
                }));
            } else {
                const err = res.data.error || {
                    code: "UNKNOWN",
                    details: res.data.message,
                };
                set((s) => ({
                    isCompressing: false,
                    videoErrors: [
                        ...s.videoErrors.filter((e) => e.nodeId !== "compress"),
                        makeError(
                            "compress",
                            res.data.message,
                            err.code,
                            err.details,
                        ),
                    ],
                }));
            }
        } catch {
            set((s) => ({
                isCompressing: false,
                videoErrors: [
                    ...s.videoErrors.filter((e) => e.nodeId !== "compress"),
                    makeError(
                        "compress",
                        "Network error",
                        "NETWORK_ERROR",
                        "Unable to reach the server. Check your connection and try again.",
                    ),
                ],
            }));
        }
    },

    dismissError: (id) => {
        set((s) => ({
            videoErrors: s.videoErrors.filter((e) => e.id !== id),
        }));
    },
}));
