import { spring, useCurrentFrame, useVideoConfig } from "remotion";

interface FocusZoomProps {
  children: React.ReactNode;
  zoomStartFrame: number;
  zoomScale: number;
  targetX: number; // 目标点 X 坐标 (0-100%)
  targetY: number; // 目标点 Y 坐标 (0-100%)
}

export const FocusZoomWrapper: React.FC<FocusZoomProps> = ({
  children,
  zoomStartFrame,
  zoomScale,
  targetX,
  targetY,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 1. 计算缩放倍率 (使用 spring 保证惯性)
  const zoomSpring = spring({
    frame: frame - zoomStartFrame,
    fps,
    config: { stiffness: 100, damping: 20 },
  });

  const scale = 1 + zoomSpring * (zoomScale - 1);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        // 2. 核心：将变换原点锁定在目标对象位置
        transformOrigin: `${targetX}% ${targetY}%`,
        // 3. 应用缩放
        transform: `scale(${scale})`,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {children}
    </div>
  );
};
