// src/Root.tsx
import { Composition } from "remotion";
import { DynamicRenderer } from "./DynamicRenderer";
import { VideoComposer } from "./VideoComposer";
import type { VideoProject } from "./types/composition";

const DEFAULT_PROJECT: VideoProject = {
  version: "1.0",
  composition: { width: 1920, height: 1080, fps: 30 },
  scenes: [
    {
      id: "placeholder",
      durationInFrames: 90,
      background: { type: "solid", color: "#0a0a0a" },
      overlays: [],
      transitionOut: { type: "cut" },
    },
  ],
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="render"
        component={DynamicRenderer}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          effectId: "blur-reveal",
          effectProps: { text: "Hello, Remotion!", color: "#ffffff" },
        }}
      />

      <Composition
        id="compose"
        component={VideoComposer}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ project: DEFAULT_PROJECT }}
      />
    </>
  );
};
