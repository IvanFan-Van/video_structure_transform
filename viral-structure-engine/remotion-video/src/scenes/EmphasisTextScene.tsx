/**
 * EmphasisTextScene — KenBurns缩放 + BGM卡点脉冲场景渲染器
 *
 * 与 TextOverlayScene 的区别:
 *   - KenBurns 微缩放效果（画面持续1.0→1.04缓慢放大，营造"紧张感"）
 *   - BGM卡点脉冲装饰线（卡点帧附近出现金色竖线，强度随距离衰减）
 *   - 字体略小（min(fontSize, 48px)），为脉冲线留出空间
 *
 * 适用场景:
 *   - 产品卖点展示（需要持续吸引注意力）
 *   - 重要信息强调（需要视觉冲击力）
 *   - CTA/结尾（需要增强记忆点）
 *
 * KenBurns 效果:
 *   scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04])
 *   → 在场景持续时间内，画面从100%缓慢放大到104%
 *
 * BGM卡点脉冲:
 *   - 找到最近的卡点帧（beatFrames 中最接近当前帧的）
 *   - 距离≤3帧 → 脉冲线 opacity = 1→0（距离越近越亮）
 *   - 脉冲线高40px × 宽3px，位于文字上方80px，金色带发光
 */
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { AnimatedText } from '../components/AnimatedText';
import { SceneBackground } from '../components/SceneBackground';
import { SceneData } from '../types';

export const EmphasisTextScene: React.FC<SceneData> = ({
  text,
  textStyle,
  backgroundColorFallback,
  backgroundVideo,
  backgroundImage,
  beatFrames,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 按标点拆句
  const sentences = text.split(/[，。！？,!?]/).filter(Boolean);
  const framesPerSentence = Math.max(
    Math.floor(durationInFrames / Math.max(sentences.length, 1)),
    8
  );
  const visibleCount = Math.min(
    Math.floor(frame / framesPerSentence) + 1,
    sentences.length
  );
  const currentIndex = Math.max(0, visibleCount - 1);
  const visibleText = sentences[currentIndex] ?? '';

  /**
   * KenBurns 微缩放: 从1.0缓慢放大到1.04
   * 模拟摄像机缓慢推进的效果，增加视觉动态感
   */
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
    extrapolateRight: 'clamp',
  });

  /**
   * BGM卡点装饰线脉冲
   *
   * 找到最近的卡点帧 → 计算距离 → 距离≤3帧则发光
   * 线位于文字上方80px（position_y - 80px），金色(#FFD700)带发光
   */
  const nearest =
    beatFrames.length > 0
      ? beatFrames.reduce((p, c) =>           // 找到最近的卡点帧
          Math.abs(c - frame) < Math.abs(p - frame) ? c : p
        )
      : -999;
  const beatDist = Math.abs(nearest - frame);  // 距离最近卡点的帧数
  const accentOpacity =
    beatDist <= 3 ? interpolate(beatDist, [0, 3], [1, 0]) : 0;  // 距离越小越亮

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        transform: `scale(${scale})`,  // KenBurns效果
      }}
    >
      {/* 三级背景 */}
      <SceneBackground
        backgroundVideo={backgroundVideo}
        backgroundImage={backgroundImage}
        backgroundColorFallback={backgroundColorFallback}
      />
      {/* BGM卡点脉冲装饰线 — 金色竖线带发光 */}
      <div
        style={{
          position: 'absolute',
          left: '50%',                        // 水平居中
          transform: 'translateX(-50%)',
          width: 3,                           // 线宽3px
          height: 40,                         // 线高40px
          backgroundColor: '#FFD700',         // 金色
          opacity: accentOpacity,             // 脉冲强度
          borderRadius: 2,
          boxShadow: `0 0 12px rgba(255,215,0,${accentOpacity})`,  // 发光效果
          top: `calc(${textStyle.position_y}% - 80px)`,  // 文字上方80px
        }}
      />
      {/* 文字层 — fontSize 限制最大48px，为脉冲线留空间 */}
      <div
        style={{
          position: 'absolute',
          left: `${textStyle.position_x}%`,
          top: `${textStyle.position_y}%`,
          transform: 'translate(-50%, -50%)',
          width: '85%',
        }}
      >
        <AnimatedText
          text={visibleText}
          animation={textStyle.animation}
          color={textStyle.color}
          fontSize={Math.min(textStyle.fontSize, 48)}  // 限制字号
          fontWeight={textStyle.fontWeight}
          beatFrames={beatFrames}
        />
      </div>
    </div>
  );
};
