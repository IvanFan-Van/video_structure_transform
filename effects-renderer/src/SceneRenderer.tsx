"use client";

import { useEffect, useState } from "react";
import { AbsoluteFill, Sequence, staticFile } from "remotion";
import type { Scene } from "./types/composition";
import { BackgroundRenderer } from "./BackgroundRenderer";
import { OverlayRenderer } from "./OverlayRenderer";

interface SceneRendererProps {
  scene: Scene;
}

export function SceneRenderer({ scene }: SceneRendererProps) {
  return (
    <AbsoluteFill>
      <BackgroundRenderer background={scene.background} />

      {scene.overlays.map((overlay) => (
        <OverlayRenderer key={overlay.id} overlay={overlay} />
      ))}

      {scene.audio && (
        <AudioLayer
          audio={scene.audio}
          sceneDuration={scene.durationInFrames}
        />
      )}
    </AbsoluteFill>
  );
}

function AudioLayer({
  audio,
  sceneDuration,
}: {
  audio: NonNullable<Scene["audio"]>;
  sceneDuration: number;
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
    <Sequence from={0} durationInFrames={sceneDuration}>
      <AudioComponent
        src={staticFile(audio.src)}
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
