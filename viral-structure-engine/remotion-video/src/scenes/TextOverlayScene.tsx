/**
 * TextOverlayScene — 逐句打字文本场景渲染器
 *
 * 渲染逻辑:
 *   1. 按标点符号（，。！？,!?）将完整文案拆分为单句
 *   2. 根据当前帧号决定显示到第几句（逐句替换模式）
 *      - 每句分配 framesPerSentence 帧（= 总帧数 / 句数）
 *      - 当前帧 → visibleCount → 只显示最后一句
 *   3. 搭配 SceneBackground（三级背景） + AnimatedText（5种动画）
 *
 * 整体替换模式 vs 累积模式:
 *   本场景使用"替换模式"（而非"累积模式"）—
 *   原视频分析确认: 多句字幕位于同一个position_y位置 = 当前句替换上一句。
 *   因此每一帧只显示当前应出现的那一句，不保留之前的句子。
 */
import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { AnimatedText } from '../components/AnimatedText';
import { SceneBackground } from '../components/SceneBackground';
import { SceneData } from '../types';

export const TextOverlayScene: React.FC<SceneData> = ({
  text,                     // 完整文案（可能含多句）
  textStyle,                // 文字样式（字号/颜色/位置/动画类型）
  backgroundColorFallback,  // 纯色背景（兜底）
  backgroundVideo,          // 视频背景（可选）
  backgroundImage,          // 图片背景（可选）
  beatFrames,               // BGM卡点相对帧号
}) => {
  const frame = useCurrentFrame();          // 当前帧号
  const { durationInFrames } = useVideoConfig();  // 场景总帧数

  // 按标点拆句: "句子1，句子2。句子3！" → ["句子1","句子2","句子3"]
  const sentences = text.split(/[，。！？,!?]/).filter(Boolean);
  // 每句分配的帧数（最少8帧，避免闪屏）
  const framesPerSentence = Math.max(
    Math.floor(durationInFrames / Math.max(sentences.length, 1)),
    8
  );
  // 当前应显示到第几句（1-indexed）
  const visibleCount = Math.min(
    Math.floor(frame / framesPerSentence) + 1,
    sentences.length
  );
  // 当前正在显示的那一句的索引
  const currentIndex = Math.max(0, visibleCount - 1);
  // 当前帧显示的文本（只显示最后一句 = 替换模式）
  const visibleText = sentences[currentIndex] ?? '';

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
      }}
    >
      {/* 三级背景 — 视频 > 图片 > 纯色 */}
      <SceneBackground
        backgroundVideo={backgroundVideo}
        backgroundImage={backgroundImage}
        backgroundColorFallback={backgroundColorFallback}
      />
      {/* 文字层 — 定位在 textStyle.position_x/position_y */}
      <div
        style={{
          position: 'absolute',
          left: `${textStyle.position_x}%`,
          top: `${textStyle.position_y}%`,
          transform: 'translate(-50%, -50%)',  // 以中心点为锚点
          width: '85%',                        // 文字宽度限制（避免贴边）
        }}
      >
        <AnimatedText
          text={visibleText}
          animation={textStyle.animation}
          color={textStyle.color}
          fontSize={textStyle.fontSize}
          fontWeight={textStyle.fontWeight}
          beatFrames={beatFrames}
        />
      </div>
    </div>
  );
};
