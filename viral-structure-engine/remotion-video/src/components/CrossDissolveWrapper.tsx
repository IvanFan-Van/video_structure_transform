/**
 * CrossDissolveWrapper — 场景间叠化过渡效果
 *
 * 通过控制 opacity（透明度）实现两个相邻场景之间的交叉淡入淡出。
 *
 * 过渡逻辑:
 *   - 第一个场景 (hasPrev=false): 开头有淡入效果 (0→1, dissolveFrames*2 帧内)
 *   - 中间场景 (hasPrev=true, hasNext=true): 开头淡入 + 结尾淡出
 *   - 最后一个场景 (hasNext=false): 结尾有淡出效果 (1→0, dissolveFrames*2 帧内)
 *
 * 参数说明:
 *   hasPrev:        是否有前一个场景（决定是否做淡入）
 *   hasNext:        是否有后一个场景（决定是否做淡出）
 *   dissolveFrames: 叠化过渡帧数，默认15帧（约0.5秒@30fps）
 */
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

interface CrossDissolveWrapperProps {
  hasPrev: boolean;           // 是否有前一个场景
  hasNext: boolean;           // 是否有后一个场景
  dissolveFrames: number;     // 过渡帧数
  children: React.ReactNode;  // 场景内容
}

export const CrossDissolveWrapper: React.FC<CrossDissolveWrapperProps> = ({
  hasPrev,
  hasNext,
  dissolveFrames,
  children,
}) => {
  const frame = useCurrentFrame();           // 当前帧号（相对该Sequence的起始帧）
  const { durationInFrames } = useVideoConfig();  // 当前Sequence的总帧数

  let opacity = 1;  // 默认不透明

  // 淡入: 如果有前一个场景，且当前帧在开头 dissolveFrames*2 范围内
  if (hasPrev && frame < dissolveFrames * 2) {
    // 从透明→不透明
    opacity = interpolate(frame, [0, dissolveFrames], [0, 1], {
      extrapolateRight: 'clamp',  // 超出范围时保持边界值
    });
  }

  // 淡出: 如果有后一个场景，且当前帧在结尾 dissolveFrames*2 范围内
  if (hasNext && frame > durationInFrames - dissolveFrames * 2) {
    // 从不透明→透明
    opacity = interpolate(
      frame,
      [durationInFrames - dissolveFrames, durationInFrames],
      [1, 0],
      { extrapolateLeft: 'clamp' }
    );
  }

  return <div style={{ width: '100%', height: '100%', opacity }}>{children}</div>;
};
