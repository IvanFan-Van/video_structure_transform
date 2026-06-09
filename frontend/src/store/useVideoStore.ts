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
    PlanResult,
    SlotFillResult,
    GenerateResult,
} from "./types";
import { useAuthStore } from "./useAuthStore";

// ─── Stream abort controllers ─────────────────────────────────────────────────

const streamControllers: Record<string, AbortController | null> = {
    audio: null,
    compress: null,
    script: null,
    split: null,
    visual: null,
    plan: null,
    slot_generate: null,
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

    planableTaskIds: {
        script: string | null;
        visual: string | null;
        audio: string | null;
        split: string | null;
    };
    effectTaskIds: Record<number, string>;

    planStatus: NodeStatus;
    planTime: number | null;
    planResult: PlanResult | null;
    planTaskId: string | null;

    slotFillStatuses: Record<string, "filling" | "filled" | "error">;

    generateStatus: NodeStatus;
    generateTime: number | null;
    generateResult: GenerateResult | null;
    generateTaskId: string | null;

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
    startPlan: (userBrief: string, targetDuration?: number) => Promise<void>;
    stopPlan: () => Promise<void>;
    quickUpload: (file: File) => Promise<string | null>;
    fillSlot: (
        planId: string,
        slotId: string,
        fillMethod: "user_upload" | "ai_generate" | "manual_input",
        value?: string,
    ) => Promise<void>;
    startSlotGenerate: () => Promise<void>;
    stopSlotGenerate: () => Promise<void>;
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

    planableTaskIds: { script: null, visual: null, audio: null, split: null },
    effectTaskIds: {},

    planStatus: "idle",
    planTime: null,
    planResult: null,
    planTaskId: null,

    slotFillStatuses: {},

    generateStatus: "idle",
    generateTime: null,
    generateResult: null,
    generateTaskId: null,

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
            planableTaskIds: {
                script: null,
                visual: null,
                audio: null,
                split: null,
            },
            effectTaskIds: {},
            planStatus: "idle",
            planTime: null,
            planResult: null,
            planTaskId: null,
            slotFillStatuses: {},
            generateStatus: "idle",
            generateTime: null,
            generateResult: null,
            generateTaskId: null,
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
                    planableTaskIds: {
                        ...get().planableTaskIds,
                        script: taskId,
                    },
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
                                planableTaskIds: {
                                    ...s.planableTaskIds,
                                    audio: taskId,
                                },
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
                    planableTaskIds: {
                        ...get().planableTaskIds,
                        visual: taskId,
                    },
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
                    planableTaskIds: {
                        ...get().planableTaskIds,
                        split: taskId,
                    },
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
                    effectTaskIds: {
                        ...get().effectTaskIds,
                        [segmentIndex]: taskId,
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

    startPlan: async (userBrief, targetDuration?) => {
        const { planableTaskIds, effectTaskIds } = get();
        const token = useAuthStore.getState().token;
        if (!token) return;
        if (!planableTaskIds.script && !planableTaskIds.visual) return;
        const t0 = Date.now();

        set({
            planStatus: "loading",
            planTime: null,
            planTaskId: null,
            planResult: null,
        });

        try {
            const body: Record<string, unknown> = { user_brief: userBrief };
            if (planableTaskIds.script)
                body.script_task_id = planableTaskIds.script;
            if (planableTaskIds.visual)
                body.visual_task_id = planableTaskIds.visual;
            if (planableTaskIds.audio)
                body.audio_task_id = planableTaskIds.audio;
            if (targetDuration != null) body.target_duration = targetDuration;
            const effectIds = Object.values(effectTaskIds).filter(Boolean);
            if (effectIds.length > 0) body.effect_task_id = effectIds[0];

            const res = await axios.post("/api/plan", body, {
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
            });

            if (res.data.status !== "success") {
                const elapsed = (Date.now() - t0) / 1000;
                const { msg, code, details } = parseApiError(
                    res.data,
                    "Plan failed",
                );
                set((s) => ({
                    planResult: null,
                    planStatus: "error",
                    planTime: elapsed,
                    videoErrors: [
                        ...s.videoErrors.filter((e) => e.nodeId !== "plan"),
                        makeError("plan", msg, code, details),
                    ],
                }));
                return;
            }

            const taskId: string = res.data.data.task_id;
            set({ planTaskId: taskId });

            await subscribeTaskStream<PlanResult>(taskId, token, {
                controllerKey: "plan",
                t0,
                set,
                nodeId: "plan",
                failureLabel: "Plan generation failed",
                onCompleted: (result, _elapsed) => ({
                    planResult: result,
                    planStatus: "success",
                    planTime: _elapsed,
                    planTaskId: null,
                }),
                onFailed: (_elapsed) => ({
                    planResult: null,
                    planStatus: "error",
                    planTime: _elapsed,
                    planTaskId: null,
                }),
                onCancelled: () => ({
                    planStatus: "idle",
                    planTaskId: null,
                }),
            });
        } catch {
            const elapsed = (Date.now() - t0) / 1000;
            set((s) => ({
                planResult: null,
                planStatus: "error",
                planTime: elapsed,
                videoErrors: [
                    ...s.videoErrors.filter((e) => e.nodeId !== "plan"),
                    makeError(
                        "plan",
                        "Network error",
                        "NETWORK_ERROR",
                        NETWORK_ERROR_DETAILS,
                    ),
                ],
            }));
        }
    },

    stopPlan: async () => {
        abortStream("plan");
        const { planTaskId } = get();
        if (planTaskId) await cancelTaskRequest(planTaskId);
        set({
            planStatus: "cancelled",
            planTaskId: null,
            planResult: null,
            planTime: null,
        });
    },

    quickUpload: async (file) => {
        const token = useAuthStore.getState().token;
        if (!token) return null;
        const formData = new FormData();
        formData.append("file", file);
        try {
            const res = await axios.post<ApiResponse<UploadResult>>(
                "/api/upload",
                formData,
                { headers: { Authorization: `Bearer ${token}` } },
            );
            if (res.data.status === "success") {
                return res.data.data.asset_id;
            }
            return null;
        } catch {
            return null;
        }
    },

    fillSlot: async (planId, slotId, fillMethod, value?) => {
        const token = useAuthStore.getState().token;
        if (!token) return;

        set((s) => ({
            slotFillStatuses: {
                ...s.slotFillStatuses,
                [slotId]: "filling" as const,
            },
        }));

        try {
            const body: Record<string, string> = { fill_method: fillMethod };
            if (value !== undefined) body.value = value;

            const res = await axios.patch<ApiResponse<SlotFillResult>>(
                `/api/plan/${planId}/slot/${slotId}`,
                body,
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (res.data.status === "success") {
                const filled = res.data.data;
                set((s) => {
                    const plan = s.planResult;
                    if (!plan)
                        return {
                            slotFillStatuses: {
                                ...s.slotFillStatuses,
                                [slotId]: "filled",
                            },
                        };

                    const segments = plan.segments.map((seg) => {
                        const si = seg.slots.findIndex(
                            (sl) => sl.slot_id === slotId,
                        );
                        if (si === -1) return seg;
                        const slots = [...seg.slots];
                        slots[si] = { ...slots[si], ...filled };
                        return { ...seg, slots };
                    });

                    return {
                        planResult: { ...plan, segments },
                        slotFillStatuses: {
                            ...s.slotFillStatuses,
                            [slotId]: "filled",
                        },
                    };
                });
            } else {
                const msg =
                    (res.data as ApiErrorResponse).message ?? "Fill failed";
                set((s) => ({
                    slotFillStatuses: {
                        ...s.slotFillStatuses,
                        [slotId]: "error",
                    },
                    videoErrors: [
                        ...s.videoErrors.filter(
                            (e) => e.nodeId !== `slot_${slotId}`,
                        ),
                        makeError(`slot_${slotId}`, msg, "FILL_FAILED", ""),
                    ],
                }));
            }
        } catch {
            set((s) => ({
                slotFillStatuses: {
                    ...s.slotFillStatuses,
                    [slotId]: "error",
                },
                videoErrors: [
                    ...s.videoErrors.filter(
                        (e) => e.nodeId !== `slot_${slotId}`,
                    ),
                    makeError(
                        `slot_${slotId}`,
                        "Network error",
                        "NETWORK_ERROR",
                        NETWORK_ERROR_DETAILS,
                    ),
                ],
            }));
        }
    },

    startSlotGenerate: async () => {
        const { planResult } = get();
        if (!planResult) return;
        const token = useAuthStore.getState().token;
        if (!token) return;
        const t0 = Date.now();

        set({
            generateStatus: "loading",
            generateTime: null,
            generateTaskId: null,
            generateResult: null,
        });

        try {
            const res = await axios.post(
                `/api/plan/${planResult.plan_id}/generate`,
                {},
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
                    "Slot generation failed",
                );
                set((s) => ({
                    generateResult: null,
                    generateStatus: "error",
                    generateTime: elapsed,
                    videoErrors: [
                        ...s.videoErrors.filter(
                            (e) => e.nodeId !== "plan_generate",
                        ),
                        makeError("plan_generate", msg, code, details),
                    ],
                }));
                return;
            }

            const taskId: string = res.data.data.task_id;
            set({ generateTaskId: taskId });

            await subscribeTaskStream<GenerateResult>(taskId, token, {
                controllerKey: "slot_generate",
                t0,
                set,
                nodeId: "plan_generate",
                failureLabel: "Slot generation failed",
                onCompleted: (result, _elapsed) => ({
                    generateResult: result,
                    generateStatus: "success",
                    generateTime: _elapsed,
                    generateTaskId: null,
                }),
                onFailed: (_elapsed) => ({
                    generateResult: null,
                    generateStatus: "error",
                    generateTime: _elapsed,
                    generateTaskId: null,
                }),
                onCancelled: () => ({
                    generateStatus: "idle",
                    generateTaskId: null,
                }),
            });

            if (get().generateStatus === "success") {
                try {
                    const planRes = await axios.get(
                        `/api/task/${planResult.plan_id}/stream`,
                        {
                            headers: {
                                Authorization: `Bearer ${token}`,
                            },
                        },
                    );
                    if (
                        planRes.data.status === "success" &&
                        planRes.data.data?.result
                    ) {
                        set({ planResult: planRes.data.data.result });
                    }
                } catch {
                    // best-effort re-fetch
                }
            }
        } catch {
            const elapsed = (Date.now() - t0) / 1000;
            set((s) => ({
                generateResult: null,
                generateStatus: "error",
                generateTime: elapsed,
                videoErrors: [
                    ...s.videoErrors.filter(
                        (e) => e.nodeId !== "plan_generate",
                    ),
                    makeError(
                        "plan_generate",
                        "Network error",
                        "NETWORK_ERROR",
                        NETWORK_ERROR_DETAILS,
                    ),
                ],
            }));
        }
    },

    stopSlotGenerate: async () => {
        abortStream("slot_generate");
        const { generateTaskId } = get();
        if (generateTaskId) await cancelTaskRequest(generateTaskId);
        set({
            generateStatus: "cancelled",
            generateTaskId: null,
            generateResult: null,
            generateTime: null,
        });
    },

    dismissError: (id) => {
        set((s) => ({
            videoErrors: s.videoErrors.filter((e) => e.id !== id),
        }));
    },
}));
