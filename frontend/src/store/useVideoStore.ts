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
    TaskInfo,
} from "./types";
import { useAuthStore } from "./useAuthStore";

const pollTimers: Record<string, ReturnType<typeof setInterval> | null> = {};

function clearPoll(taskId: string | null) {
    if (!taskId) return;
    const timer = pollTimers[taskId];
    if (timer) {
        clearInterval(timer);
        pollTimers[taskId] = null;
    }
}

function clearAllPolls() {
    Object.keys(pollTimers).forEach(clearPoll);
}

function pollTask(
    taskId: string,
    token: string | null,
    onDone: (info: TaskInfo) => void,
    onReject: () => void,
) {
    clearPoll(taskId);

    const doPoll = async () => {
        try {
            const res = await axios.get<ApiResponse<TaskInfo>>(
                `/api/task/${taskId}`,
                { headers: { Authorization: `Bearer ${token}` } },
            );
            const task = res.data as any;
            if (task.status !== "success") return;
            const info: TaskInfo = task.data;
            if (
                info.status === "completed" ||
                info.status === "failed" ||
                info.status === "cancelled"
            ) {
                clearPoll(taskId);
                onDone(info);
            }
        } catch {
            clearPoll(taskId);
            onReject();
        }
    };

    pollTimers[taskId] = setInterval(doPoll, 1500);
    setTimeout(doPoll, 500);
}

interface VideoState {
    isUploading: boolean;
    uploadProgress: number;
    uploadResult: UploadResult | null;
    thumbnailUrl: string | null;

    compressConfig: CompressConfig;

    isCompressing: boolean;
    compressTaskId: string | null;
    compressResult: CompressResult | null;

    scriptStatus: string;
    scriptTime: number | null;
    isExtractingFlow: boolean;
    extractTaskId: string | null;
    transcriptResult: TranscriptResult | null;

    videoErrors: NodeError[];
}

interface VideoActions {
    uploadVideo: (file: File) => Promise<void>;
    setCompressConfig: (
        updater: CompressConfig | ((c: CompressConfig) => CompressConfig),
    ) => void;
    startCompress: () => Promise<void>;
    stopCompress: () => Promise<void>;
    startExtractScript: () => Promise<void>;
    stopExtractScript: () => Promise<void>;
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
            video.currentTime = 1;
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

    videoErrors: [],

    uploadVideo: async (file) => {
        const token = useAuthStore.getState().token;
        clearAllPolls();
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
        set({ isCompressing: true, compressResult: null, compressTaskId: null });

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
                    code = res.data.code ? String(res.data.code) : "SERVER_ERROR";
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

            pollTask(
                taskId,
                token,
                (info) => {
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
                    } else {
                        set({
                            isCompressing: false,
                            compressTaskId: null,
                        });
                    }
                },
                () => {
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
                },
            );
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
        const { compressTaskId } = get();
        if (!compressTaskId) return;
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
        clearPoll(compressTaskId);
        set({
            isCompressing: false,
            compressTaskId: null,
            compressResult: null,
        });
    },

    startExtractScript: async () => {
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
                    code = res.data.code ? String(res.data.code) : "SERVER_ERROR";
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

            pollTask(
                taskId,
                token,
                (info) => {
                    const elapsed = (Date.now() - t0) / 1000;
                    if (info.status === "completed") {
                        set((s) => ({
                            transcriptResult: info.result,
                            scriptStatus: "done",
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
                    } else {
                        set({
                            scriptStatus: "idle",
                            extractTaskId: null,
                        });
                    }
                },
                () => {
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
                },
            );
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
                        "Unable to reach the server. Check your connection and try again.",
                    ),
                ],
            }));
        }
    },

    stopExtractScript: async () => {
        const { extractTaskId } = get();
        if (!extractTaskId) return;
        const token = useAuthStore.getState().token;
        try {
            await axios.post(
                `/api/task/${extractTaskId}/cancel`,
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
        clearPoll(extractTaskId);
        set({
            isExtractingFlow: false,
            scriptStatus: "idle",
            extractTaskId: null,
            transcriptResult: null,
            scriptTime: null,
        });
    },

    dismissError: (id) => {
        set((s) => ({
            videoErrors: s.videoErrors.filter((e) => e.id !== id),
        }));
    },
}));
