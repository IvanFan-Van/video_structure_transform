// =============================================================================
// computeTimeline — pre-compute global frame positions for each scene
// =============================================================================
// For non-blend transitions, each scene renders fully for its duration.
// Transition segments are inserted BETWEEN scenes as standalone segments.
// Scene N starts at: prevScene.endFrame + prevTransitionDuration
// Transition N starts at: sceneN.endFrame (immediately after scene N)

import type { Scene, SceneTransition } from "../types/composition";

export interface ComputedScene {
  /** Scene id from JSON */
  id: string;
  /** Original scene data */
  scene: Scene;
  /** Global frame where this scene's content begins */
  globalStartFrame: number;
  /** Global frame where this scene's content ends (exclusive) */
  globalEndFrame: number;
  /** Index in the original scenes array */
  index: number;
}

export interface ComputedTransition {
  /** "scenes[N].id -> scenes[N+1].id" */
  id: string;
  /** Transition config */
  transition: SceneTransition & { type: "effect" };
  /** Global frame where the transition begins */
  globalStartFrame: number;
  /** Global frame where the transition ends (exclusive) */
  globalEndFrame: number;
}

export interface ComputedTimeline {
  scenes: ComputedScene[];
  transitions: ComputedTransition[];
  totalDurationInFrames: number;
}

export function computeTimeline(scenes: Scene[]): ComputedTimeline {
  const computedScenes: ComputedScene[] = [];
  const computedTransitions: ComputedTransition[] = [];

  let cursor = 0;

  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];

    const globalStartFrame = cursor;
    const globalEndFrame = cursor + scene.durationInFrames;

    computedScenes.push({
      id: scene.id,
      scene,
      globalStartFrame,
      globalEndFrame,
      index: i,
    });

    cursor = globalEndFrame;

    // Handle transition out (except for last scene)
    if (i < scenes.length - 1) {
      const transition = scene.transitionOut;

      if (transition.type === "effect") {
        const transStartFrame = cursor;
        const transEndFrame = cursor + transition.durationInFrames;

        computedTransitions.push({
          id: `${scene.id} -> ${scenes[i + 1].id}`,
          transition: transition as SceneTransition & { type: "effect" },
          globalStartFrame: transStartFrame,
          globalEndFrame: transEndFrame,
        });

        cursor = transEndFrame;
      }
      // "cut" has no transition segment, cursor doesn't move
    }
  }

  return {
    scenes: computedScenes,
    transitions: computedTransitions,
    totalDurationInFrames: cursor,
  };
}
