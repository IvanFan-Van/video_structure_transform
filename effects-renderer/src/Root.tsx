// src/Root.tsx
import { Composition } from "remotion";
import { DynamicRenderer } from "./DynamicRenderer";

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
    </>
  );
};
