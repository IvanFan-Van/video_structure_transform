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
    SplitConfig,
    SplitResult,
    EffectResult,
} from "./types";
import { useAuthStore } from "./useAuthStore";

// ─── Stream abort controllers ─────────────────────────────────────────────────

const streamControllers: Record<string, AbortController | null> = {
    audio: null,
    compress: null,
    script: null,
    split: null,
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

    const elapsed = () => (Date.now() - t0) / 1000;
    const filterErrors = (errors: NodeError[]) =>
        errors.filter((e: NodeError) => e.nodeId !== nodeId);

    const setNetworkError = () => {
        set((s: any) => ({
            ...opts.onFailed(elapsed()),
            videoErrors: [
                ...filterErrors(s.videoErrors),
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
        await fetchEventSource(`/api/task/${taskId}/stream`, {
            headers: { Authorization: `Bearer ${token ?? ""}` },
            signal,
            onopen: async (response) => {
                if (!response.ok) {
                    setNetworkError();
                    throw new Error("Bad response status");
                }
            },
            onmessage: (event) => {
                if (!event.data) return;
                try {
                    const info: TaskInfo = JSON.parse(event.data);
                    switch (info.status) {
                        case "completed":
                            set((s: any) => ({
                                ...opts.onCompleted(
                                    info.result as TResult,
                                    elapsed(),
                                ),
                                videoErrors: filterErrors(s.videoErrors),
                            }));
                            abortStream(controllerKey); // 主动关闭，阻止重连
                            break;
                        case "failed":
                            set((s: any) => ({
                                ...opts.onFailed(elapsed()),
                                videoErrors: [
                                    ...filterErrors(s.videoErrors),
                                    makeError(
                                        nodeId,
                                        failureLabel,
                                        "TASK_FAILED",
                                        info.error ?? "",
                                    ),
                                ],
                            }));
                            abortStream(controllerKey);
                            break;
                        case "cancelled":
                            set(opts.onCancelled());
                            abortStream(controllerKey);
                            break;
                    }
                } catch {
                    // Malformed JSON — skip
                }
            },
            onerror: (err) => {
                if (err?.name === "AbortError") throw err; // 让库停止，不触发 setNetworkError
                setNetworkError();
                throw err; // 抛出阻止自动重试
            },
        });
    } catch (err: any) {
        // AbortError 和 FatalError 都会冒泡到这里，忽略即可
    }
}

// ─── State & actions interfaces ───────────────────────────────────────────────

interface VideoState {
    isUploading: boolean;
    uploadProgress: number;
    uploadResult: UploadResult | null;

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

    splitConfig: SplitConfig;
    splitStatus: NodeStatus;
    splitTime: number | null;
    isSplitting: boolean;
    splitTaskId: string | null;
    splitResult: SplitResult | null;

    effectStatuses: Record<number, NodeStatus>;
    effectResults: Record<number, EffectResult | null>;

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
    setSplitConfig: (
        updater: SplitConfig | ((c: SplitConfig) => SplitConfig),
    ) => void;
    startSplit: () => Promise<void>;
    stopSplit: () => Promise<void>;
    analyzeEffect: (assetId: string, segmentIndex: number) => Promise<void>;
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

const initialSplitConfig: SplitConfig = {
    use_ai: false,
    threshold: 25,
    min_scene_len: 15,
};

// ─── Store ────────────────────────────────────────────────────────────────────

export const useVideoStore = create<VideoState & VideoActions>((set, get) => ({
    isUploading: false,
    uploadProgress: 0,
    uploadResult: null,

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

    splitConfig: { ...initialSplitConfig },
    splitStatus: "idle",
    splitTime: null,
    isSplitting: false,
    splitTaskId: null,
    splitResult: null,

    effectStatuses: {},
    effectResults: {},

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

    setSplitConfig: (updater) => {
        set((s) => ({
            splitConfig:
                typeof updater === "function"
                    ? updater(s.splitConfig)
                    : updater,
        }));
    },

    startSplit: async () => {
        const { compressResult, splitConfig } = get();
        if (!compressResult) return;
        const token = useAuthStore.getState().token;
        const t0 = Date.now();

        set({
            isSplitting: true,
            splitStatus: "loading",
            splitTime: null,
            splitTaskId: null,
            splitResult: null,
        });

        try {
            const res = await axios.post(
                "/api/split",
                { asset_id: compressResult.asset_id, ...splitConfig },
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
                    "Split failed",
                );
                set((s) => ({
                    isSplitting: false,
                    splitStatus: "error",
                    videoErrors: [
                        ...s.videoErrors.filter((e) => e.nodeId !== "split"),
                        makeError("split", msg, code, details),
                    ],
                }));
                return;
            }

            const taskId: string = res.data.data.task_id;
            set({ splitTaskId: taskId });

            await subscribeTaskStream<SplitResult>(taskId, token, {
                controllerKey: "split",
                t0,
                set,
                nodeId: "split",
                failureLabel: "Split failed",
                onCompleted: (result, elapsed) => ({
                    splitResult: result,
                    splitStatus: "success",
                    splitTime: elapsed,
                    isSplitting: false,
                    splitTaskId: null,
                }),
                onFailed: (elapsed) => ({
                    splitResult: null,
                    splitStatus: "error",
                    splitTime: elapsed,
                    isSplitting: false,
                    splitTaskId: null,
                }),
                onCancelled: () => ({
                    splitStatus: "idle",
                    splitTaskId: null,
                    isSplitting: false,
                }),
            });
        } catch {
            set((s) => ({
                isSplitting: false,
                splitStatus: "error",
                videoErrors: [
                    ...s.videoErrors.filter((e) => e.nodeId !== "split"),
                    makeError(
                        "split",
                        "Network error",
                        "NETWORK_ERROR",
                        NETWORK_ERROR_DETAILS,
                    ),
                ],
            }));
        }
    },

    stopSplit: async () => {
        abortStream("split");
        const { splitTaskId } = get();
        if (splitTaskId) await cancelTaskRequest(splitTaskId);
        set({
            isSplitting: false,
            splitStatus: "cancelled",
            splitTaskId: null,
            splitResult: null,
            splitTime: null,
        });
    },

    analyzeEffect: async (assetId, segmentIndex) => {
        const token = useAuthStore.getState().token;
        const t0 = Date.now();
        const controllerKey = `effect_${segmentIndex}`;

        set((s) => ({
            effectStatuses: { ...s.effectStatuses, [segmentIndex]: "loading" },
            effectResults: { ...s.effectResults, [segmentIndex]: null },
        }));

        try {
            const res = await axios.post(
                "/api/analyze-effect",
                { asset_id: assetId },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (res.data.status !== "success") {
                const elapsed = (Date.now() - t0) / 1000;
                set((s) => ({
                    effectStatuses: {
                        ...s.effectStatuses,
                        [segmentIndex]: "error",
                    },
                }));
                return;
            }

            const taskId: string = res.data.data.task_id;

            await subscribeTaskStream<EffectResult>(taskId, token, {
                controllerKey,
                t0,
                set,
                nodeId: `effect_segment_${segmentIndex}`,
                failureLabel: "Effect analysis failed",
                onCompleted: (result, elapsed) => ({
                    effectResults: {
                        ...get().effectResults,
                        [segmentIndex]: result,
                    },
                    effectStatuses: {
                        ...get().effectStatuses,
                        [segmentIndex]: "success" as NodeStatus,
                    },
                }),
                onFailed: (elapsed) => ({
                    effectStatuses: {
                        ...get().effectStatuses,
                        [segmentIndex]: "error" as NodeStatus,
                    },
                }),
                onCancelled: () => ({
                    effectStatuses: {
                        ...get().effectStatuses,
                        [segmentIndex]: "idle" as NodeStatus,
                    },
                }),
            });
        } catch {
            set((s) => ({
                effectStatuses: {
                    ...s.effectStatuses,
                    [segmentIndex]: "error",
                },
                videoErrors: [
                    ...s.videoErrors.filter(
                        (e) => e.nodeId !== `effect_segment_${segmentIndex}`,
                    ),
                    makeError(
                        `effect_segment_${segmentIndex}`,
                        "Network error",
                        "NETWORK_ERROR",
                        NETWORK_ERROR_DETAILS,
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
