export interface Preset {
    label: string;
    desc: string;
    file: string;
    data: string | null;
}

export interface DatasetInfo {
    numDocs: number;
    vocabSize: number;
    chars: string[];
    sampleDocs: string[];
}

export interface ModelConfig {
    n_embd: number;
    n_head: number;
    n_layer: number;
    block_size: number;
    num_steps: number;
    learning_rate: number;
    seed: number;
    [key: string]: number;
}

export interface RunHistoryItem {
    id: number;
    config: ModelConfig;
    finalLoss: number;
    totalTime: number;
    samples: string[];
}

export interface LossData {
    step: number;
    loss: number;
}

export interface Pos {
    x: number;
    y: number;
    w: number;
    h: number;
}

export interface VideoMeta {
    filepath: string;
    codec: string | null;
    width: number | null;
    height: number | null;
    fps: number | null;
    v_bitrate: number | null;
    total_bitrate: number | null;
    audio_sample_rate: number | null;
    audio_channels: number | null;
    a_bitrate: number | null;
    size: number | null;
    duration: number | null;
}

export interface UploadResult {
    asset_id: string;
    type: string;
    path: string;
    metadata: VideoMeta;
}

export interface CompressResult {
    asset_id: string;
    source_asset_id: string;
    type: string;
    path: string;
    metadata: VideoMeta;
}

export interface CompressConfig {
    vcodec: string;
    crf: number | null;
    target_v_bitrate: string | null;
    scale_width: number | null;
    max_fps: number | null;
    acodec: string;
    target_a_bitrate: string;
}

export interface NodeError {
    id: number;
    nodeId: string;
    message: string;
    code: string;
    details: string;
}

export interface ApiSuccessResponse<T> {
    status: "success";
    data: T;
}

export interface ApiErrorResponse {
    status: "fail" | "error";
    message: string;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;
