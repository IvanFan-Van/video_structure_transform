// src/Root.tsx
import { Composition } from "remotion";
import { DynamicRenderer } from "./DynamicRenderer";
import { EFFECT_REGISTRY } from "./effects";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {Object.entries(EFFECT_REGISTRY).map(([effectId, meta]) => (
        <Composition
          key={effectId}
          id={`effect-${effectId}`} // composition id 唯一
          component={DynamicRenderer}
          durationInFrames={meta.defaultDurationInFrames}
          fps={meta.defaultFps}
          width={meta.defaultWidth}
          height={meta.defaultHeight}
          defaultProps={{
            effectId,
            effectProps: {},
          }}
        />
      ))}

      {/* 或者注册一个万能的 dynamic composition，通过 inputProps 完全控制 */}
      <Composition
        id="dynamic"
        component={DynamicRenderer}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ effectId: "blur-reveal", effectProps: {} }}
      />
    </>
  );
};
