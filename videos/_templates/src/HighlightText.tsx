import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface HighlightProps {
  children: React.ReactNode; // 这里传入你的文字内容
  color?: string; // 高亮颜色
  delay?: number; // 延迟开始（帧）
  duration?: number; // 动画持续时间（帧）
}

export const HighlightText: React.FC<HighlightProps> = ({
  children,
  color = "rgba(255, 255, 0, 0.5)", // 默认黄色半透明
  delay = 0,
  duration = 30,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 1. 弹簧动画，让滑出的速度更有质感
  const progress = spring({
    frame: frame - delay,
    fps,
    config: { stiffness: 100, damping: 20 },
    durationInFrames: duration,
  });

  // 2. 将 0-1 的进度映射到 0%-100% 的宽度
  const width = interpolate(progress, [0, 1], [0, 100]);

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      {/* 高亮色块层 */}
      <div
        style={{
          position: "absolute",
          bottom: "10%",
          left: 0,
          height: "40%", // 高亮块高度，可调整
          width: `${width}%`, // 核心：宽度随进度变化
          backgroundColor: color,
          zIndex: -1, // 放在文字后面
          borderRadius: "4px",
        }}
      />
      {/* 原始文字层 */}
      {children}
    </div>
  );
};
