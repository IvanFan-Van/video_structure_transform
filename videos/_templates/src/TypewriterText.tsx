import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

interface TypewriterProps {
  text: string;
  speed?: number; // 每秒显示的字符数，默认 5
  fontSize?: number; // 字号，默认 100
  color?: string; // 文字颜色，默认 white
  fontFamily?: string; // 字体，默认 sans-serif
}

export const TypewriterText: React.FC<TypewriterProps> = ({
  text,
  speed = 5,
  fontSize = 100,
  color = "white",
  fontFamily = "sans-serif",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 根据帧数计算当前应显示的字符数
  const charCount = Math.floor(frame / (fps / speed));
  const displayedText = text.slice(0, charCount);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        color: color,
        fontSize: `${fontSize}px`,
        fontFamily: fontFamily,
        fontWeight: "bold",
        textShadow: "0 0 10px rgba(255, 255, 255, 0.5)",
      }}
    >
      {displayedText}
    </AbsoluteFill>
  );
};
