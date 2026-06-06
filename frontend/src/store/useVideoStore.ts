import { create } from "zustand";
import axios, { AxiosError } from "axios";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import {
    UploadResult,
    CompressResult,
    CompressConfig,
    NodeError,
    ApiResponse,
    ApiErrorResponse,
    TranscriptResult,
    TaskInfo,
    AudioStreamChunk,
    AudioGlobalFeatures,
    VisualResult,
    NodeStatus,
} from "./types";
import { useAuthStore } from "./useAuthStore";

// ─── Stream abort controllers ─────────────────────────────────────────────────

const streamControllers: Record<string, AbortController | null> = {
    audio: null,
    compress: null,
    script: null,
    visual: null,
};

function abortStream(key: string) {
    streamControllers[key]?.abort();
    streamControllers[key] = null;
}

function abortAllStreams() {
    Object.keys(streamControllers).forEach(abortStream);
}

// ─── Shared helpers ───────────────────────────────────────────────────────────

function makeError(
    nodeId: string,
    message: string,
    code: string,
    details: string,
): NodeError {
    return { id: Date.now(), nodeId, message, code, details };
}

const NETWORK_ERROR_DETAILS =
    "Unable to reach the server. Check your connection and try again.";

function parseApiError(
    data: any,
    fallbackMessage: string,
): { msg: string; code: string; details: string } {
    if (data?.status === "error") {
        return {
            msg: data.message || fallbackMessage,
            code: data.code ? String(data.code) : "SERVER_ERROR",
            details: data.data
                ? JSON.stringify(data.data, null, 2)
                : data.message || "",
        };
    }
    return {
        msg: data?.data?.message || fallbackMessage,
        code: "VALIDATION_ERROR",
        details: JSON.stringify(data?.data, null, 2),
    };
}

async function cancelTaskRequest(taskId: string) {
    const token = useAuthStore.getState().token;
    try {
        await axios.post(
            `/api/task/${taskId}/cancel`,
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

// ─── Universal task stream subscriber ────────────────────────────────────────

interface TaskStreamOptions<TResult> {
    controllerKey: string;
    t0: number;
    set: (updater: any) => void;
    nodeId: string;
    failureLabel: string;
    onCompleted: (result: TResult, elapsed: number) => object;
    onFailed: (elapsed: number) => object;
    onCancelled: () => object;
}

async function subscribeTaskStream<TResult>(
    taskId: string,
    token: string | null,
    opts: TaskStreamOptions<TResult>,
) {
    const { controllerKey, t0, set, nodeId, failureLabel } = opts;

    abortStream(controllerKey);
    streamControllers[controllerKey] = new AbortController();
    const signal = streamControllers[controllerKey]!.signal;

    const setNetworkError = (elapsed: number) => {
        set((s: any) => ({
            ...opts.onFailed(elapsed),
            videoErrors: [
                ...s.videoErrors.filter((e: NodeError) => e.nodeId !== nodeId),
                makeError(
                    nodeId,
                    "Network error",
                    "NETWORK_ERROR",
                    NETWORK_ERROR_DETAILS,
                ),
            ],
        }));
    };

    try {
        const response = await fetch(`/api/task/${taskId}/stream`, {
            headers: { Authorization: `Bearer ${token}` },
            signal,
        });

        if (!response.ok || !response.body) {
            setNetworkError((Date.now() - t0) / 1000);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        outer: while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";

            for (const raw of lines) {
                const line = raw.trim();
                if (
                    !line ||
                    line.startsWith(":") ||
                    /^(event|id|retry):/.test(line)
                )
                    continue;

                const jsonStr = line.startsWith("data:")
                    ? line.slice(5).trim()
                    : line;
                if (!jsonStr) continue;

                try {
                    const info: TaskInfo = JSON.parse(jsonStr);
                    const elapsed = (Date.now() - t0) / 1000;

                    if (info.status === "completed") {
                        set((s: any) => ({
                            ...opts.onCompleted(
                                info.result as TResult,
                                elapsed,
                            ),
                            videoErrors: s.videoErrors.filter(
                                (e: NodeError) => e.nodeId !== nodeId,
                            ),
                        }));
                        break outer;
                    } else if (info.status === "failed") {
                        set((s: any) => ({
                            ...opts.onFailed(elapsed),
                            videoErrors: [
                                ...s.videoErrors.filter(
                                    (e: NodeError) => e.nodeId !== nodeId,
                                ),
                                makeError(
                                    nodeId,
                                    failureLabel,
                                    "TASK_FAILED",
                                    info.error || "",
                                ),
                            ],
                        }));
                        break outer;
                    } else if (info.status === "cancelled") {
                        set(opts.onCancelled());
                        break outer;
                    }
                } catch {
                    // Malformed JSON line — skip
                }
            }
        }
    } catch (err: any) {
        if (err?.name === "AbortError") return;
        setNetworkError((Date.now() - t0) / 1000);
    }
}

// ─── Misc helpers ─────────────────────────────────────────────────────────────

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

// ─── State & actions interfaces ───────────────────────────────────────────────

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
    stopAnalyzeAudio: () => void;
    startAnalyzeVisual: () => Promise<void>;
    stopAnalyzeVisual: () => Promise<void>;
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

// ─── Store ────────────────────────────────────────────────────────────────────

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
    isAnalyzingVisual: false,
    visualTaskId: null,
    visualResult: null,

    videoErrors: [],

    // ── Actions ────────────────────────────────────────────────────────────────

    uploadVideo: async (file) => {
        const token = useAuthStore.getState().token;
        abortAllStreams();

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
            let msg = "Network error";
            let code = "NETWORK_ERROR";
            let details = NETWORK_ERROR_DETAILS;

            if (axios.isAxiosError(error)) {
                const axiosError = error as AxiosError<ApiErrorResponse>;
                if (axiosError.response) {
                    msg = axiosError.response.statusText;
                    code = axiosError.response.statusText;
                    details = JSON.stringify(axiosError.response.data);
                }
            }

            set((s) => ({
                isUploading: false,
                videoErrors: [
                    ...s.videoErrors.filter((e) => e.nodeId !== "reference"),
                    makeError("reference", msg, code, details),
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
        const t0 = Date.now();

        set({
            isCompressing: true,
            compressResult: null,
            compressTaskId: null,
        });

        try {
            const res = await axios.post(
                "/api/compress",
                { asset_id: uploadResult.asset_id, ...compressConfig },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (res.data.status !== "success") {
                const { msg, code, details } = parseApiError(
                    res.data,
                    "Compress failed",
                );
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

            await subscribeTaskStream<CompressResult>(taskId, token, {
                controllerKey: "compress",
                t0,
                set,
                nodeId: "compress",
                failureLabel: "Compress failed",
                onCompleted: (result) => ({
                    compressResult: result,
                    isCompressing: false,
                    compressTaskId: null,
                }),
                onFailed: () => ({
                    isCompressing: false,
                    compressTaskId: null,
                }),
                onCancelled: () => ({
                    isCompressing: false,
                    compressTaskId: null,
                }),
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
                        NETWORK_ERROR_DETAILS,
                    ),
                ],
            }));
        }
    },

    stopCompress: async () => {
        abortStream("compress");
        const { compressTaskId } = get();
        if (compressTaskId) await cancelTaskRequest(compressTaskId);
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
                const { msg, code, details } = parseApiError(
                    res.data,
                    "Extract failed",
                );
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

            await subscribeTaskStream<TranscriptResult>(taskId, token, {
                controllerKey: "script",
                t0,
                set,
                nodeId: "extracting",
                failureLabel: "Extract failed",
                onCompleted: (result, elapsed) => ({
                    transcriptResult: result,
                    scriptStatus: "success",
                    scriptTime: elapsed,
                    extractTaskId: null,
                }),
                onFailed: (elapsed) => ({
                    transcriptResult: null,
                    scriptStatus: "error",
                    scriptTime: elapsed,
                    extractTaskId: null,
                }),
                onCancelled: () => ({
                    scriptStatus: "idle",
                    extractTaskId: null,
                }),
            });
        } catch {
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
                        NETWORK_ERROR_DETAILS,
                    ),
                ],
            }));
        }
    },

    stopAnalyzeScript: async () => {
        abortStream("script");
        const { extractTaskId } = get();
        if (extractTaskId) await cancelTaskRequest(extractTaskId);
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

        // Audio uses a dedicated streaming endpoint with frame-by-frame data —
        // not the generic task-poll pattern, so it keeps its own handler.
        abortStream("audio");
        streamControllers["audio"] = new AbortController();

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
                const { msg, code, details } = parseApiError(
                    res.data,
                    "Audio analysis failed",
                );
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

            await fetchEventSource(`/api/task/${taskId}/stream`, {
                headers: { Authorization: `Bearer ${token}` },
                signal: streamControllers["audio"]!.signal,
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
                    } catch {
                        // Malformed frame — skip
                    }
                },
                onerror() {
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
                },
            });
        } catch {
            // Aborted or connection error — onerror already handled the error state.
        }
    },

    stopAnalyzeAudio: () => {
        abortStream("audio");
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
                const { msg, code, details } = parseApiError(
                    res.data,
                    "Visual analysis failed",
                );
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

            await subscribeTaskStream<VisualResult>(taskId, token, {
                controllerKey: "visual",
                t0,
                set,
                nodeId: "visual",
                failureLabel: "Visual analysis failed",
                onCompleted: (result, elapsed) => ({
                    visualResult: result,
                    visualStatus: "success",
                    visualTime: elapsed,
                    isAnalyzingVisual: false,
                    visualTaskId: null,
                }),
                onFailed: (elapsed) => ({
                    visualResult: null,
                    visualStatus: "error",
                    visualTime: elapsed,
                    isAnalyzingVisual: false,
                    visualTaskId: null,
                }),
                onCancelled: () => ({
                    visualStatus: "idle",
                    visualTaskId: null,
                    isAnalyzingVisual: false,
                }),
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
                        NETWORK_ERROR_DETAILS,
                    ),
                ],
            }));
        }
    },

    stopAnalyzeVisual: async () => {
        abortStream("visual");
        const { visualTaskId } = get();
        if (visualTaskId) await cancelTaskRequest(visualTaskId);
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
