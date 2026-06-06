import { create } from "zustand";
import axios, { AxiosError } from "axios";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import {
    UploadResult,
    CompressResult,
    CompressConfig,
    NodeError,
    ApiResponse,
    VideoMeta,
    ApiErrorResponse,
    TranscriptResult,
    TaskInfo,
    AudioStreamChunk,
    AudioGlobalFeatures,
    VisualResult,
    NodeStatus,
} from "./types";
import { useAuthStore } from "./useAuthStore";

let sseAbortController: AbortController | null = null;
let compressSseController: AbortController | null = null;
let scriptSseController: AbortController | null = null;
let visualSseController: AbortController | null = null;

interface VideoState {
    isUploading: boolean;
    uploadProgress: number;
    uploadResult: UploadResult | null;
    thumbnailUrl: string | null;

    compressConfig: CompressConfig;

    isCompressing: boolean;
    compressTaskId: string | null;
    compressResult: CompressResult | null;

    scriptStatus: NodeStatus;
    scriptTime: number | null;
    isExtractingFlow: boolean;
    extractTaskId: string | null;
    transcriptResult: TranscriptResult | null;

    audioStatus: NodeStatus;
    audioTime: number | null;
    audioTaskId: string | null;
    streamArr: AudioStreamChunk[];
    audioGlobal: AudioGlobalFeatures | null;
    audioBgmAssetId: string | null;

    visualStatus: NodeStatus;
    visualTime: number | null;
    isAnalyzingVisual: boolean;
    visualTaskId: string | null;
    visualResult: VisualResult | null;

    videoErrors: NodeError[];
}

interface VideoActions {
    uploadVideo: (file: File) => Promise<void>;
    setCompressConfig: (
        updater: CompressConfig | ((c: CompressConfig) => CompressConfig),
    ) => void;
    startCompress: () => Promise<void>;
    stopCompress: () => Promise<void>;
    startAnalyzeScript: () => Promise<void>;
    stopAnalyzeScript: () => Promise<void>;
    startAnalyzeAudio: () => Promise<void>;
    stopAnalyzeAudio: () => Promise<void>;
    startAnalyzeVisual: () => Promise<void>;
    stopAnalyzeVisual: () => void;
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
        video.onloadeddata = () => {
            video.currentTime = Math.min(1, video.duration / 2);
        };
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
    compressTaskId: null,
    compressResult: null,

    scriptStatus: "idle",
    scriptTime: null,
    isExtractingFlow: false,
    extractTaskId: null,
    transcriptResult: null,

    audioStatus: "idle",
    audioTime: null,
    audioTaskId: null,
    streamArr: [],
    audioGlobal: null,
    audioBgmAssetId: null,
    visualStatus: "idle",
    visualTime: null,
    visualResult: null,
    isAnalyzingVisual: false,
    visualTaskId: null,

    videoErrors: [],

    uploadVideo: async (file) => {
        const token = useAuthStore.getState().token;
        if (sseAbortController) {
            sseAbortController.abort();
            sseAbortController = null;
        }
        if (compressSseController) {
            compressSseController.abort();
            compressSseController = null;
        }
        if (scriptSseController) {
            scriptSseController.abort();
            scriptSseController = null;
        }
        if (visualSseController) {
            visualSseController.abort();
            visualSseController = null;
        }
        set({
            isUploading: true,
            uploadProgress: 0,
            uploadResult: null,
            compressResult: null,
            compressTaskId: null,
            transcriptResult: null,
            extractTaskId: null,
            scriptTime: null,
            scriptStatus: "idle",
            isExtractingFlow: false,
            isCompressing: false,
            audioStatus: "idle",
            audioTime: null,
            audioTaskId: null,
            streamArr: [],
            audioGlobal: null,
            audioBgmAssetId: null,
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
        set({
            isCompressing: true,
            compressResult: null,
            compressTaskId: null,
        });

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

            if (res.data.status !== "success") {
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
                return;
            }

            const taskId: string = res.data.data.task_id;
            set({ compressTaskId: taskId });

            if (compressSseController) compressSseController.abort();
            compressSseController = new AbortController();

            await fetchEventSource(`/api/task/${taskId}/stream`, {
                headers: { Authorization: `Bearer ${token}` },
                signal: compressSseController.signal,
                onmessage(event) {
                    try {
                        const info: TaskInfo = JSON.parse(event.data);
                        if (info.status === "completed") {
                            set((s) => ({
                                compressResult: info.result,
                                isCompressing: false,
                                compressTaskId: null,
                                videoErrors: s.videoErrors.filter(
                                    (e) => e.nodeId !== "compress",
                                ),
                            }));
                        } else if (info.status === "failed") {
                            set((s) => ({
                                isCompressing: false,
                                compressTaskId: null,
                                videoErrors: [
                                    ...s.videoErrors.filter(
                                        (e) => e.nodeId !== "compress",
                                    ),
                                    makeError(
                                        "compress",
                                        "Compress failed",
                                        "COMPRESS_FAILED",
                                        info.error || "",
                                    ),
                                ],
                            }));
                        } else if (info.status === "cancelled") {
                            set({
                                isCompressing: false,
                                compressTaskId: null,
                            });
                        }
                    } catch {}
                },
                onerror() {
                    set((s) => ({
                        isCompressing: false,
                        compressTaskId: null,
                        videoErrors: [
                            ...s.videoErrors.filter(
                                (e) => e.nodeId !== "compress",
                            ),
                            makeError(
                                "compress",
                                "Network error",
                                "NETWORK_ERROR",
                                "Unable to reach the server. Check your connection and try again.",
                            ),
                        ],
                    }));
                    throw new Error("stop");
                },
            });
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

    stopCompress: async () => {
        if (compressSseController) {
            compressSseController.abort();
            compressSseController = null;
        }
        const { compressTaskId } = get();
        if (compressTaskId) {
            const token = useAuthStore.getState().token;
            try {
                await axios.post(
                    `/api/task/${compressTaskId}/cancel`,
                    {},
                    {
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                    },
                );
            } catch {
                // best-effort cancel
            }
        }
        set({
            isCompressing: false,
            compressTaskId: null,
            compressResult: null,
        });
    },

    startAnalyzeScript: async () => {
        const { compressResult } = get();
        if (!compressResult) return;
        const token = useAuthStore.getState().token;
        const t0 = Date.now();
        set({
            isExtractingFlow: true,
            scriptStatus: "loading",
            scriptTime: null,
            extractTaskId: null,
            transcriptResult: null,
        });

        try {
            const res = await axios.post(
                "/api/analyze-script",
                { asset_id: compressResult.asset_id },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (res.data.status !== "success") {
                const elapsed = (Date.now() - t0) / 1000;
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
                    scriptTime: elapsed,
                    videoErrors: [
                        ...s.videoErrors.filter(
                            (e) => e.nodeId !== "extracting",
                        ),
                        makeError("extracting", msg, code, details),
                    ],
                }));
                return;
            }

            const taskId: string = res.data.data.task_id;
            set({ extractTaskId: taskId });

            if (scriptSseController) scriptSseController.abort();
            scriptSseController = new AbortController();

            let retryCount = 0;
            const MAX_RETRIES = 5;

            await fetchEventSource(`/api/task/${taskId}/stream`, {
                headers: { Authorization: `Bearer ${token}` },
                signal: scriptSseController.signal,
                openWhenHidden: false,
                onmessage(event) {
                    try {
                        const info: TaskInfo = JSON.parse(event.data);
                        const elapsed = (Date.now() - t0) / 1000;
                        if (info.status === "completed") {
                            set((s) => ({
                                transcriptResult: info.result,
                                scriptStatus: "success",
                                scriptTime: elapsed,
                                extractTaskId: null,
                                videoErrors: s.videoErrors.filter(
                                    (e) => e.nodeId !== "extracting",
                                ),
                            }));
                        } else if (info.status === "failed") {
                            set((s) => ({
                                transcriptResult: null,
                                scriptStatus: "error",
                                scriptTime: elapsed,
                                extractTaskId: null,
                                videoErrors: [
                                    ...s.videoErrors.filter(
                                        (e) => e.nodeId !== "extracting",
                                    ),
                                    makeError(
                                        "extracting",
                                        "Extract failed",
                                        "EXTRACT_FAILED",
                                        info.error || "",
                                    ),
                                ],
                            }));
                        } else if (info.status === "cancelled") {
                            set({
                                scriptStatus: "idle",
                                extractTaskId: null,
                            });
                        }
                    } catch {}
                },
                onerror() {
                    retryCount++;
                    if (retryCount > MAX_RETRIES) {
                        const elapsed = (Date.now() - t0) / 1000;
                        set((s) => ({
                            transcriptResult: null,
                            scriptStatus: "error",
                            scriptTime: elapsed,
                            extractTaskId: null,
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
                        throw new Error("stop");
                    }
                },
            });
        } catch (error: any) {
            const elapsed = (Date.now() - t0) / 1000;
            set((s) => ({
                transcriptResult: null,
                scriptStatus: "error",
                scriptTime: elapsed,
                extractTaskId: null,
                videoErrors: [
                    ...s.videoErrors.filter((e) => e.nodeId !== "extracting"),
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

    stopAnalyzeScript: async () => {
        if (scriptSseController) {
            scriptSseController.abort();
            scriptSseController = null;
        }
        const { extractTaskId } = get();
        if (extractTaskId) {
            const token = useAuthStore.getState().token;
            try {
                await axios.post<ApiResponse<String>>(
                    `/api/task/${extractTaskId}/cancel`,
                    {},
                    {
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                    },
                );
            } catch (error: any) {
                if (axios.isAxiosError(error)) {
                    const axiosError = error as AxiosError<ApiErrorResponse>;
                    const msg =
                        axiosError.message || "Failed to cancel analysis";
                    const code = error.response?.statusText || "CANCEL_FAILED";
                    const details = axiosError.response?.data.message || "";
                    set((s) => ({
                        videoErrors: [
                            ...s.videoErrors.filter(
                                (e) => e.nodeId !== "extracting",
                            ),
                            makeError("extracting", msg, code, details),
                        ],
                    }));
                }
            }
        }
        set({
            scriptStatus: "cancelled",
            extractTaskId: null,
            transcriptResult: null,
            scriptTime: null,
        });
    },

    startAnalyzeAudio: async () => {
        const { compressResult } = get();
        if (!compressResult) return;
        const token = useAuthStore.getState().token;
        if (!token) return;
        const t0 = Date.now();

        if (sseAbortController) sseAbortController.abort();
        sseAbortController = new AbortController();

        set({
            audioStatus: "loading",
            audioTime: null,
            audioTaskId: null,
            streamArr: [],
            audioGlobal: null,
            audioBgmAssetId: null,
        });

        try {
            const res = await axios.post(
                "/api/analyze-audio",
                { asset_id: compressResult.asset_id },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (res.data.status !== "success") {
                const elapsed = (Date.now() - t0) / 1000;
                let msg: string, code: string, details: string;
                if (res.data.status === "error") {
                    msg = res.data.message || "Audio analysis failed";
                    code = res.data.code
                        ? String(res.data.code)
                        : "SERVER_ERROR";
                    details = res.data.data
                        ? JSON.stringify(res.data.data, null, 2)
                        : res.data.message || "";
                } else {
                    msg = res.data.data?.message || "Audio analysis failed";
                    code = "VALIDATION_ERROR";
                    details = JSON.stringify(res.data.data, null, 2);
                }
                set((s) => ({
                    audioGlobal: null,
                    audioStatus: "error",
                    audioTime: elapsed,
                    videoErrors: [
                        ...s.videoErrors.filter((e) => e.nodeId !== "audio"),
                        makeError("audio", msg, code, details),
                    ],
                }));
                return;
            }

            const taskId: string = res.data.data.task_id;
            set({ audioTaskId: taskId });
            let retryCount = 0;
            const MAX_RETRIES = 5;

            await fetchEventSource(`/api/task/${taskId}/stream`, {
                headers: { Authorization: `Bearer ${token}` },
                signal: sseAbortController.signal,
                openWhenHidden: false,
                onmessage(event) {
                    try {
                        const data = JSON.parse(event.data);

                        if (data.asset_id) {
                            set({ audioBgmAssetId: data.asset_id });
                        }

                        if (data.local) {
                            const chunk: AudioStreamChunk = {
                                time: data.time,
                                frame_index: data.frame_index,
                                rms: data.local.rms,
                                spectral_centroid: data.local.spectral_centroid,
                                spectral_flux: data.local.spectral_flux,
                                onset_envelope: data.local.onset_envelope,
                            };
                            set((s) => ({
                                streamArr: [...s.streamArr, chunk],
                            }));
                        }

                        if (data.running_global) {
                            set({ audioGlobal: data.running_global });
                        }

                        if (data.status === "completed") {
                            const elapsed = (Date.now() - t0) / 1000;
                            set((s) => ({
                                audioStatus: "success",
                                audioTime: elapsed,
                                audioTaskId: null,
                                audioGlobal: data.result || data.running_global,
                                videoErrors: s.videoErrors.filter(
                                    (e) => e.nodeId !== "audio",
                                ),
                            }));
                        } else if (data.status === "failed") {
                            const elapsed = (Date.now() - t0) / 1000;
                            set((s) => ({
                                audioStatus: "error",
                                audioTime: elapsed,
                                audioTaskId: null,
                                videoErrors: [
                                    ...s.videoErrors.filter(
                                        (e) => e.nodeId !== "audio",
                                    ),
                                    makeError(
                                        "audio",
                                        "Audio analysis failed",
                                        "AUDIO_FAILED",
                                        data.error || "",
                                    ),
                                ],
                            }));
                        } else if (data.status === "cancelled") {
                            set({
                                audioStatus: "idle",
                                audioTaskId: null,
                            });
                        }
                    } catch {}
                },
                onerror() {
                    retryCount++;
                    if (retryCount > MAX_RETRIES) {
                        const elapsed = (Date.now() - t0) / 1000;
                        set((s) => ({
                            audioStatus: "error",
                            audioTime: elapsed,
                            audioTaskId: null,
                            videoErrors: [
                                ...s.videoErrors.filter(
                                    (e) => e.nodeId !== "audio",
                                ),
                                makeError(
                                    "audio",
                                    "Audio analysis failed",
                                    "AUDIO_FAILED",
                                    "Stream connection error or server error.",
                                ),
                            ],
                        }));
                        throw new Error("stop");
                    }
                },
            });
        } catch {
            // aborted or connection error — onerror already handled error case
        }
    },

    stopAnalyzeAudio: async () => {
        if (sseAbortController) {
            sseAbortController.abort();
            sseAbortController = null;
        }
        const { audioTaskId } = get();
        if (audioTaskId) {
            const token = useAuthStore.getState().token;
            try {
                await axios.post(
                    `/api/task/${audioTaskId}/cancel`,
                    {},
                    {
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                    },
                );
            } catch {
                // best-effort cancel
            }
        }
        set({
            audioStatus: "cancelled",
            audioTaskId: null,
            audioTime: null,
            streamArr: [],
            audioGlobal: null,
            audioBgmAssetId: null,
        });
    },

    startAnalyzeVisual: async () => {
        const { compressResult } = get();
        if (!compressResult) return;
        const token = useAuthStore.getState().token;
        const t0 = Date.now();
        set({
            isAnalyzingVisual: true,
            visualStatus: "loading",
            visualTime: null,
            visualTaskId: null,
            visualResult: null,
        });

        try {
            const res = await axios.post(
                "/api/analyze-visual",
                { asset_id: compressResult.asset_id },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (res.data.status !== "success") {
                const elapsed = (Date.now() - t0) / 1000;
                let msg: string, code: string, details: string;
                if (res.data.status === "error") {
                    msg = res.data.message || "Visual analysis failed";
                    code = res.data.code
                        ? String(res.data.code)
                        : "SERVER_ERROR";
                    details = res.data.data
                        ? JSON.stringify(res.data.data, null, 2)
                        : res.data.message || "";
                } else {
                    msg = res.data.data?.message || "Visual analysis failed";
                    code = "VALIDATION_ERROR";
                    details = JSON.stringify(res.data.data, null, 2);
                }
                set((s) => ({
                    visualResult: null,
                    visualStatus: "error",
                    visualTime: elapsed,
                    isAnalyzingVisual: false,
                    videoErrors: [
                        ...s.videoErrors.filter((e) => e.nodeId !== "visual"),
                        makeError("visual", msg, code, details),
                    ],
                }));
                return;
            }

            const taskId: string = res.data.data.task_id;
            set({ visualTaskId: taskId });

            if (visualSseController) visualSseController.abort();
            visualSseController = new AbortController();

            let retryCount = 0;
            const MAX_RETRIES = 5;

            await fetchEventSource(`/api/task/${taskId}/stream`, {
                headers: { Authorization: `Bearer ${token}` },
                signal: visualSseController.signal,
                openWhenHidden: false,
                onmessage(event) {
                    try {
                        const info: TaskInfo = JSON.parse(event.data);
                        const elapsed = (Date.now() - t0) / 1000;
                        if (info.status === "completed") {
                            set((s) => ({
                                visualResult: info.result,
                                visualStatus: "success",
                                visualTime: elapsed,
                                isAnalyzingVisual: false,
                                visualTaskId: null,
                                videoErrors: s.videoErrors.filter(
                                    (e) => e.nodeId !== "visual",
                                ),
                            }));
                        } else if (info.status === "failed") {
                            set((s) => ({
                                visualResult: null,
                                visualStatus: "error",
                                visualTime: elapsed,
                                isAnalyzingVisual: false,
                                visualTaskId: null,
                                videoErrors: [
                                    ...s.videoErrors.filter(
                                        (e) => e.nodeId !== "visual",
                                    ),
                                    makeError(
                                        "visual",
                                        "Visual analysis failed",
                                        "EXTRACT_FAILED",
                                        info.error || "",
                                    ),
                                ],
                            }));
                        } else if (info.status === "cancelled") {
                            set({
                                visualStatus: "idle",
                                visualTaskId: null,
                                isAnalyzingVisual: false,
                            });
                        }
                    } catch {}
                },
                onerror() {
                    retryCount++;
                    if (retryCount > MAX_RETRIES) {
                        const elapsed = (Date.now() - t0) / 1000;
                        set((s) => ({
                            visualResult: null,
                            visualStatus: "error",
                            visualTime: elapsed,
                            isAnalyzingVisual: false,
                            visualTaskId: null,
                            videoErrors: [
                                ...s.videoErrors.filter(
                                    (e) => e.nodeId !== "visual",
                                ),
                                makeError(
                                    "visual",
                                    "Network error",
                                    "NETWORK_ERROR",
                                    "Unable to reach the server. Check your connection and try again.",
                                ),
                            ],
                        }));
                        throw new Error("stop");
                    }
                },
            });
        } catch {
            const elapsed = (Date.now() - t0) / 1000;
            set((s) => ({
                visualResult: null,
                visualStatus: "error",
                visualTime: elapsed,
                isAnalyzingVisual: false,
                visualTaskId: null,
                videoErrors: [
                    ...s.videoErrors.filter((e) => e.nodeId !== "visual"),
                    makeError(
                        "visual",
                        "Network error",
                        "NETWORK_ERROR",
                        "Unable to reach the server. Check your connection and try again.",
                    ),
                ],
            }));
        }
    },

    stopAnalyzeVisual: async () => {
        if (visualSseController) {
            visualSseController.abort();
            visualSseController = null;
        }
        const { visualTaskId } = get();
        if (visualTaskId) {
            const token = useAuthStore.getState().token;
            try {
                await axios.post(
                    `/api/task/${visualTaskId}/cancel`,
                    {},
                    {
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                    },
                );
            } catch {
                // best-effort cancel
            }
        }
        set({
            isAnalyzingVisual: false,
            visualStatus: "cancelled",
            visualTaskId: null,
            visualResult: null,
            visualTime: null,
        });
    },

    dismissError: (id) => {
        set((s) => ({
            videoErrors: s.videoErrors.filter((e) => e.id !== id),
        }));
    },
}));
