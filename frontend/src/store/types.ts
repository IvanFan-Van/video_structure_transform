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
    cover_image_asset_id?: string | null;
    metadata: VideoMeta;
}

export interface CompressResult {
    asset_id: string;
    source_asset_id: string;
    type: string;
    path: string;
    cover_image_asset_id?: string | null;
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

export interface AudioAnalysisResult {
    audio_asset_id: string;
    bgm_path: string;
    duration: number;
    genre: string;
    bpm: number;
    beat_timings: number[];
    energy_curve: number[];
    spectral_centroid: number[];
    spectral_centroid_mean: number;
    spectral_flux: number[];
    onset_envelope: number[];
    dynamic_range: number;
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
    text_elements?: VisualTextElement[];
}

export interface VisualTransition {
    after_shot_index: number;
    type: string;
    duration: number;
}

export interface VisualTextElement {
    text: string;
    position: string | null;
    appear_time: number;
    disappear_time: number;
    font_size: number | null;
    font_weight: string | null;
    font_color: string | null;
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

export interface SplitConfig {
    use_ai: boolean;
    threshold: number;
    min_scene_len: number;
}

export interface SplitSegment {
    index: number;
    start_sec: number;
    end_sec: number;
    duration: number;
    cut_score: number | null;
    reason: string | null;
}

export interface SplitClipAsset {
    asset_id: string;
    cover_image_asset_id?: string | null;
    index: number;
    path: string;
    metadata: {
        codec: string | null;
        width: number | null;
        height: number | null;
        fps: number | null;
        duration: number | null;
    };
}

export interface SplitResult {
    source_asset_id: string;
    method: string;
    total_segments: number;
    segments: SplitSegment[];
    clip_assets: SplitClipAsset[];
}

export interface EffectItem {
    name: string;
    evidence: string;
}

export interface EffectParamItem {
    effect_name: string;
    remocn_component: string;
    remocn_props: Record<string, unknown>;
    timing_start: number;
    timing_duration: number;
    applies_to: string;
    evidence: string;
}

export interface EffectParamResult {
    observations: string;
    param_set: EffectParamItem[];
}

export interface EffectResult {
    observations: string;
    effects: EffectItem[];
}

export interface PlanSlot {
    slot_id: string;
    slot_type: string;
    description: string;
    constraints: Record<string, unknown>;
    status: string;
    fill_method: string | null;
    value: string | null;
}

export interface PlanSegment {
    index: number;
    stage: string;
    start_time: number;
    end_time: number;
    narrative_intent: string;
    hook_type: string | null;
    cta_type: string | null;
    slots: PlanSlot[];
}

export interface PlanBgmSpec {
    genre: string;
    bpm: number;
    mood: string;
    reference_audio_asset_id?: string;
}

export interface PlanResult {
    plan_id: string;
    user_brief: string;
    reference_asset_id: string;
    estimated_duration: number;
    narrator_perspective: string;
    bgm_spec: PlanBgmSpec;
    segments: PlanSegment[];
    created_at: string;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

export interface SlotFillResult {
    slot_id: string;
    slot_type: string;
    description: string;
    constraints: Record<string, unknown>;
    status: "filled" | "pending";
    fill_method: "user_upload" | "ai_generate" | "manual_input";
    value: string | null;
}

export interface GeneratedSlot {
    slot_id: string;
    slot_type: string;
    stage: string;
    success: boolean;
    value: string | null;
    prompt: string | null;
    error: string | null;
}

export interface GenerateResult {
    generated: number;
    generated_slots: GeneratedSlot[];
}

export interface StyleOption {
    name: string;
    label: string;
    description: string;
}

export interface PreviewItem {
    style: string;
    label: string;
    description: string;
    still_path: string;
    duration_frames: number;
    scene_count: number;
}

export interface RenderResult {
    style?: string;
    asset_id: string;
    path: string;
    duration: number;
    fps: number;
    width: number;
    height: number;
    cover_image_asset_id?: string | null;
}

export interface RenderProgress {
    phase:
        | "loading"
        | "bgm"
        | "tts"
        | "building"
        | "rendering"
        | "saving"
        | "error";
    message?: string;
    progress?: number;
    frame?: number;
    totalFrames?: number;
}
