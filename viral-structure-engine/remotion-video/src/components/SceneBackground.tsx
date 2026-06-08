/**
 * SceneBackground — 三级背景素材渲染
 *
 * 优先级:
 *   1. backgroundVideo — 用户提供的视频素材（OffthreadVideo，H.264硬件加速）
 *   2. backgroundImage  — 用户提供的图片素材（Img组件）
 *   3. backgroundColorFallback — 纯色背景（最可靠的后备方案）
 *
 * 所有背景都是绝对定位的满屏覆盖层（objectFit: cover）。
 * staticFile() 将文件名转为 public/ 目录下的绝对路径。
 */
import React from "react";
import { OffthreadVideo, Img, staticFile } from "remotion";

const FULL_SCREEN: React.CSSProperties = {
  position: "absolute",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  objectFit: "cover",    // 裁剪填充，保持宽高比
};

export const SceneBackground: React.FC<{
  backgroundVideo: string | null;      // 视频文件名（已拷贝到 public/）
  backgroundImage: string | null;      // 图片文件名（已拷贝到 public/）
  backgroundColorFallback: string;     // 纯色背景 hex（兜底方案）
}> = ({ backgroundVideo, backgroundImage, backgroundColorFallback }) => {
  // Level 1: 视频背景
  if (backgroundVideo) {
    return (
      <OffthreadVideo src={staticFile(backgroundVideo)} style={FULL_SCREEN} />
    );
  }
  // Level 2: 图片背景
  if (backgroundImage) {
    return <Img src={staticFile(backgroundImage)} style={FULL_SCREEN} />;
  }
  // Level 3: 纯色背景（永远可用）
  return (
    <div
      style={{ ...FULL_SCREEN, backgroundColor: backgroundColorFallback }}
    />
  );
};
