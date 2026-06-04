import { create } from "zustand";
import axios, { AxiosError } from "axios";
import {
    UploadResult,
    CompressResult,
    CompressConfig,
    NodeError,
    ApiResponse,
    VideoMeta,
    ApiErrorResponse,
    TranscriptResult,
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

    scriptStatus: string;
    isExtractingFlow: boolean;
    transcriptResult: TranscriptResult | null;

    videoErrors: NodeError[];
}

interface VideoActions {
    uploadVideo: (file: File) => Promise<void>;
    setCompressConfig: (
        updater: CompressConfig | ((c: CompressConfig) => CompressConfig),
    ) => void;
    startCompress: () => Promise<void>;
    startExtractScript: () => Promise<void>;
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

    scriptStatus: "idle",
    isExtractingFlow: false,
    transcriptResult: null,

    videoErrors: [],

    uploadVideo: async (file) => {
        const token = useAuthStore.getState().token;
        set({
            isUploading: true,
            uploadProgress: 0,
            uploadResult: null,
            compressResult: null,
            transcriptResult: null,
            scriptStatus: "idle",
            isExtractingFlow: false,
        });

        generateThumbnail(file).then((url) => set({ thumbnailUrl: url }));

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await axios.post<ApiResponse<UploadResult>>(
                "/api/upload",
                formData,
                {
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
                },
            );

            const result = res.data;

            if (result.status !== "success") {
                throw new Error("服务器 status 字段与 status code 不一致");
            }

            set((s) => ({
                uploadResult: result.data,
                isUploading: false,
                uploadProgress: 100,
                videoErrors: s.videoErrors.filter(
                    (e) => e.nodeId !== "reference",
                ),
            }));
        } catch (error: any) {
            if (axios.isAxiosError(error)) {
                const axiosError = error as AxiosError<ApiErrorResponse>;
                if (axiosError.response) {
                    const res = axiosError.response;
                    const result = res.data;

                    let msg: string, code: string, details: string;
                    msg = res.statusText;
                    code = res.statusText;
                    details = JSON.stringify(result);

                    set((s) => ({
                        isUploading: false,
                        videoErrors: [
                            ...s.videoErrors.filter(
                                (e) => e.nodeId !== "reference",
                            ),
                            makeError("reference", msg, code, details),
                        ],
                    }));
                    return;
                }
            }

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
            if (res.data.status === "success") {
                set((s) => ({
                    compressResult: res.data.data,
                    isCompressing: false,
                    videoErrors: s.videoErrors.filter(
                        (e) => e.nodeId !== "compress",
                    ),
                }));
            } else {
                let msg: string, code: string, details: string;
                if (res.data.status === "error") {
                    msg = res.data.message || "Compress failed";
                    code = res.data.code
                        ? String(res.data.code)
                        : "SERVER_ERROR";
                    details = res.data.data
                        ? JSON.stringify(res.data.data, null, 2)
                        : res.data.message || "";
                } else {
                    msg = res.data.data?.message || "Compress failed";
                    code = "VALIDATION_ERROR";
                    details = JSON.stringify(res.data.data, null, 2);
                }
                set((s) => ({
                    isCompressing: false,
                    videoErrors: [
                        ...s.videoErrors.filter((e) => e.nodeId !== "compress"),
                        makeError("compress", msg, code, details),
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

    startExtractScript: async () => {
        const { compressResult } = get();
        if (!compressResult) return;
        const token = useAuthStore.getState().token;
        set({
            isExtractingFlow: true,
            scriptStatus: "loading",
            transcriptResult: null,
        });

        try {
            const res = await axios.post(
                "/api/extract-transcript",
                { asset_id: compressResult.asset_id },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );
            if (res.data.status === "success") {
                set((s) => ({
                    transcriptResult: res.data.data,
                    scriptStatus: "done",
                    videoErrors: s.videoErrors.filter(
                        (e) => e.nodeId !== "extracting",
                    ),
                }));
            } else {
                let msg: string, code: string, details: string;
                if (res.data.status === "error") {
                    msg = res.data.message || "Extract failed";
                    code = res.data.code
                        ? String(res.data.code)
                        : "SERVER_ERROR";
                    details = res.data.data
                        ? JSON.stringify(res.data.data, null, 2)
                        : res.data.message || "";
                } else {
                    msg = res.data.data?.message || "Extract failed";
                    code = "VALIDATION_ERROR";
                    details = JSON.stringify(res.data.data, null, 2);
                }
                set((s) => ({
                    transcriptResult: null,
                    scriptStatus: "error",
                    videoErrors: [
                        ...s.videoErrors.filter(
                            (e) => e.nodeId !== "extracting",
                        ),
                        makeError("extracting", msg, code, details),
                    ],
                }));
            }
        } catch {
            set((s) => ({
                transcriptResult: null,
                scriptStatus: "error",
                videoErrors: [
                    ...s.videoErrors.filter(
                        (e) => e.nodeId !== "extracting",
                    ),
                    makeError(
                        "extracting",
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
