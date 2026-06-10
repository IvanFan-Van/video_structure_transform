// =============================================================================
// VideoComposition JSON Schema — TypeScript type definitions
// =============================================================================

export interface VideoProject {
  version: "1.0";
  composition: CompositionConfig;
  assets?: AssetRegistry;
  globalAudio?: AudioTrack;
  scenes: Scene[];
}

export interface CompositionConfig {
  width: number;
  height: number;
  fps: number;
  outputFormat?: "mp4";
  backgroundColor?: string;
}

export interface AssetRegistry {
  videos?: Record<string, VideoClip>;
  images?: Record<string, ImageClip>;
  audios?: Record<string, AudioClip>;
}

export interface VideoClip {
  src: string;
  trimStart?: number;
  trimDuration?: number;
}

export interface ImageClip {
  src: string;
}

export interface AudioClip {
  src: string;
}

// =============================================================================
// Background
// =============================================================================

export type Background =
  | { type: "solid"; color: string }
  | { type: "gradient"; colors: string[]; angle?: number }
  | { type: "video"; src: string; fit?: "cover" | "contain" | "fill"; volume?: number; loop?: boolean; trimStart?: number; trimDuration?: number }
  | { type: "image"; src: string; fit?: "cover" | "contain" | "fill" }
  | { type: "effect"; effectId: string; effectProps?: Record<string, unknown> }
  | { type: "none" };

// =============================================================================
// Overlay
// =============================================================================

export interface OverlayPosition {
  x: number | "left" | "center" | "right";
  y: number | "top" | "center" | "bottom";
}

export type Overlay =
  | {
      type: "effect";
      id: string;
      startFrame: number;
      durationInFrames: number;
      zIndex?: number;
      position: OverlayPosition;
      width?: number;
      height?: number;
      opacity?: number;
      rotation?: number;
      scale?: number;
      effectId: string;
      effectProps: Record<string, unknown>;
    }
  | {
      type: "image";
      id: string;
      startFrame: number;
      durationInFrames: number;
      zIndex?: number;
      position: OverlayPosition;
      width?: number;
      height?: number;
      opacity?: number;
      rotation?: number;
      scale?: number;
      src: string;
      fit?: "cover" | "contain" | "fill";
    }
  | {
      type: "video";
      id: string;
      startFrame: number;
      durationInFrames: number;
      zIndex?: number;
      position: OverlayPosition;
      width?: number;
      height?: number;
      opacity?: number;
      rotation?: number;
      scale?: number;
      src: string;
      fit?: "cover" | "contain" | "fill";
      volume?: number;
      loop?: boolean;
      trimStart?: number;
      trimDuration?: number;
    };

// =============================================================================
// Transition
// =============================================================================

export type SceneTransition =
  | { type: "cut" }
  | {
      type: "effect";
      effectId: string;
      durationInFrames: number;
      effectProps?: Record<string, unknown>;
    };

// =============================================================================
// Scene
// =============================================================================

export interface Scene {
  id: string;
  durationInFrames: number;
  background: Background;
  overlays: Overlay[];
  transitionOut: SceneTransition;
  audio?: AudioTrack;
}

// =============================================================================
// Audio
// =============================================================================

export interface AudioTrack {
  src: string;
  volume?: number;
  loop?: boolean;
  startFrom?: number;
  trimDuration?: number;
}
