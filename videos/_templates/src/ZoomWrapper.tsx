import { spring, useCurrentFrame, useVideoConfig } from "remotion";

interface ZoomWrapperProps {
  children: React.ReactNode;
  zoomStartFrame: number; // 从第几帧开始放大
  zoomScale?: number; // 放大倍数，默认 2 倍
}

export const ZoomWrapper: React.FC<ZoomWrapperProps> = ({
  children,
  zoomStartFrame,
  zoomScale = 2,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 使用 spring 函数，stiffness 和 damping 决定了动作的“冲击力”
  // stiffness 越高，动作越快；damping 越低，结尾晃动感越强（弹簧效果）
  const zoomSpring = spring({
    frame: frame - zoomStartFrame,
    fps,
    config: {
      stiffness: 150,
      damping: 15,
    },
  });

  // 将 spring 的 0-1 变化映射到 1 到 targetScale
  const scale = 1 + zoomSpring * (zoomScale - 1);

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        transformOrigin: "center center", // 默认从中心放大，可改为 '50% 50%' 或具体坐标
        width: "100%",
        height: "100%",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {children}
    </div>
  );
};
