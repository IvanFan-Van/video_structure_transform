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

export type NodeStatus = "idle" | "loading" | "success" | "error" | "cancelled";

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

export interface TranscriptStage {
    visual_text: string;
    audio_text: string;
    start_time: number;
    end_time: number;
    emotional_tone: string | null;
    hook_type: string | null;
    cta_type: string | null;
}

export interface TranscriptResult {
    narrator_perspective: string | null;
    narrator_perspective_note: string | null;
    stages: {
        hook: TranscriptStage | null;
        setup: TranscriptStage | null;
        story: TranscriptStage | null;
        insight: TranscriptStage | null;
        cta: TranscriptStage | null;
        outro: TranscriptStage | null;
    };
}

export interface AudioStreamChunk {
    time: number;
    frame_index: number;
    rms: number;
    spectral_centroid: number;
    spectral_flux: number;
    onset_envelope: number;
}

export interface AudioGlobalFeatures {
    duration: number;
    genre: string;
    average_spectral_centroid: number;
    overall_brightness_hz: number;
    dynamic_range: number;
    estimated_bpm: number;
    audio_asset_id?: string;
    bgm_path?: string;
}

export interface VisualPacing {
    avg_shot_duration: number;
    pacing_category: string;
    acceleration_points: number[];
}

export interface VisualShot {
    shot_index: number;
    start_time: number;
    end_time: number;
    camera_movement: string | null;
    is_text_frame: boolean;
    description: string;
}

export interface VisualTransition {
    after_shot_index: number;
    type: string;
    duration: number;
}

export interface VisualTextElement {
    text: string;
    position: string | null;
    appear_style: string | null;
    appear_time: number;
    disappear_time: number;
    emphasis: string | null;
}

export interface VisualTextDensityPoint {
    time: number;
    text_count: number;
}

export interface VisualResult {
    total_duration: number;
    pacing: VisualPacing;
    shots: VisualShot[];
    transitions: VisualTransition[];
    text_elements: VisualTextElement[];
    text_density_curve: VisualTextDensityPoint[];
}

export type TaskStatus = "running" | "completed" | "failed" | "cancelled";

export interface TaskInfo {
    task_id: string;
    type: string;
    resource_id: string;
    status: string;
    created_at: string;
    result?: any;
    error?: string;
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
