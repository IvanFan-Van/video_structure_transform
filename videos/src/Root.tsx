import "./index.css";
import { Composition } from "remotion";
import { TypewriterText } from "./TypewriterText";
import { ZoomWrapper } from "./ZoomWrapper";
import { FocusZoomWrapper } from "./FocusZoom";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MyVideo"
        component={() => (
          <FocusZoomWrapper
            zoomStartFrame={30} // 假设在第40帧开始缩放
            zoomScale={4} // 放大1.5倍
            targetX={70} // 聚焦在屏幕正中间
            targetY={50}
          >
            <TypewriterText text="那天我问了个问题?" speed={12} color="black" />
          </FocusZoomWrapper>
        )}
        durationInFrames={60}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
