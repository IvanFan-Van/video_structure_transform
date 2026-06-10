"use client";

import { useMemo, useEffect, useState } from "react";
import { AbsoluteFill, Sequence } from "remotion";
import type { VideoProject } from "./types/composition";
import { computeTimeline } from "./lib/timeline";
import { SceneRenderer } from "./SceneRenderer";

export function VideoComposer(props: Record<string, unknown>) {
  const project = props.project as VideoProject;

  const timeline = useMemo(
    () => computeTimeline(project.scenes),
    [project.scenes],
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: project.composition.backgroundColor ?? "#000",
      }}
    >
      {project.globalAudio && (
        <GlobalAudioLayer
          audio={project.globalAudio}
          duration={timeline.totalDurationInFrames}
        />
      )}

      {timeline.scenes.map((cs) => (
        <Sequence
          key={cs.id}
          from={cs.globalStartFrame}
          durationInFrames={cs.globalEndFrame - cs.globalStartFrame}
          layout="none"
        >
          <SceneRenderer scene={cs.scene} />
        </Sequence>
      ))}

      {timeline.transitions.map((ct) => (
        <Sequence
          key={ct.id}
          from={ct.globalStartFrame}
          durationInFrames={ct.globalEndFrame - ct.globalStartFrame}
          layout="none"
        >
          <TransitionSegment
            effectId={ct.transition.effectId}
            effectProps={ct.transition.effectProps ?? {}}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
}

function TransitionSegment({
  effectId,
  effectProps,
}: {
  effectId: string;
  effectProps: Record<string, unknown>;
}) {
  const [Component, setComponent] = useState<React.ComponentType<any> | null>(
    null,
  );

  useEffect(() => {
    const mod = require("./effects") as {
      EFFECT_REGISTRY: Record<
        string,
        { component: React.ComponentType<any> }
      >;
    };
    const meta = mod.EFFECT_REGISTRY[effectId];
    if (meta) {
      setComponent(() => meta.component);
    }
  }, [effectId]);

  if (!Component) {
    return <AbsoluteFill style={{ backgroundColor: "#000" }} />;
  }

  return (
    <AbsoluteFill>
      <Component {...effectProps} />
    </AbsoluteFill>
  );
}

function GlobalAudioLayer({
  audio,
  duration,
}: {
  audio: NonNullable<VideoProject["globalAudio"]>;
  duration: number;
}) {
  const [AudioComponent, setAudioComponent] =
    useState<React.ComponentType<any> | null>(null);

  useEffect(() => {
    import("remotion").then((m) => {
      setAudioComponent(() => m.Audio);
    });
  }, []);

  if (!AudioComponent) return null;

  return (
    <Sequence from={0} durationInFrames={duration}>
      <AudioComponent
        src={audio.src}
        volume={audio.volume ?? 1}
        startFrom={
          audio.startFrom !== undefined
            ? Math.round(audio.startFrom * 30)
            : undefined
        }
        endAt={
          audio.startFrom !== undefined && audio.trimDuration !== undefined
            ? Math.round((audio.startFrom + audio.trimDuration) * 30)
            : undefined
        }
      />
    </Sequence>
  );
}
