/**
 * VideoComposition — 主视频组合组件
 *
 * 职责: 将场景列表按时间线排列，叠加音频轨道，包裹叠化转场。
 *
 * 渲染逻辑:
 *   1. 播放 BGM（背景音乐，从原视频分离的伴奏，音量35%）
 *   2. 播放 voiceover（TTS旁白，音量100%）
 *   3. 每个 scene 渲染为一个 Remotion <Sequence>（按 startFrame 自动排列）
 *   4. 每个 Sequence 包裹 CrossDissolveWrapper（场景间叠化过渡效果）
 *   5. 根据 scene.type 选择不同的场景渲染器:
 *      - text_overlay → TextOverlayScene（逐句打字文本）
 *      - emphasis_text → EmphasisTextScene（KenBurns缩放+卡点脉冲）
 *      - remocn_composed → RemocnScene（59个视觉组件）
 *
 * Sequence 特性:
 *   from:           该 scene 在视频时间线中的起始帧
 *   durationInFrames: 该 scene 的持续帧数
 *   当时间线到达 from 帧时，scene 开始渲染；超过 durationInFrames 帧后自动消失。
 */
import React from 'react';
import { Sequence, Audio, staticFile } from 'remotion';
import { TextOverlayScene } from './scenes/TextOverlayScene';
import { EmphasisTextScene } from './scenes/EmphasisTextScene';
import { RemocnScene } from './scenes/RemocnScene';
import { CrossDissolveWrapper } from './components/CrossDissolveWrapper';
import { RemotionProps, SceneData } from './types';

/**
 * 场景渲染器 — 根据 scene.type 选择正确的 React 组件
 */
const SceneRenderer: React.FC<{ scene: SceneData }> = ({ scene }) => {
  if (scene.type === 'emphasis_text') {
    return <EmphasisTextScene {...scene} />;     // KenBurns + BGM卡点脉冲
  }
  if (scene.type === 'remocn_composed') {
    return <RemocnScene {...scene} />;           // 59个remocn视觉组件
  }
  return <TextOverlayScene {...scene} />;        // 默认: 逐句打字文本
};

/**
 * 主组合组件
 *
 * @param scenes        场景列表（从remotion_props.json读取）
 * @param bgmPath       BGM文件名（public/目录下的相对路径）
 * @param voiceoverPath TTS旁白文件名（public/目录下的相对路径）
 */
export const VideoComposition: React.FC<RemotionProps> = ({ scenes, bgmPath, voiceoverPath }) => {
  return (
    <>
      {/* BGM 背景音乐 — 从原视频分离的伴奏轨道，低音量（35%）作为氛围 */}
      {bgmPath && (
        <Audio src={staticFile(bgmPath)} volume={0.35} />
      )}
      {/* TTS 旁白 — edge-tts 生成的中文语音，满音量 */}
      {voiceoverPath && (
        <Audio src={staticFile(voiceoverPath)} volume={1.0} />
      )}
      {/* 场景时间线 — 每个scene为一个Sequence，按startFrame自动排列 */}
      {scenes.map((scene, index) => (
        <Sequence
          key={scene.id}
          from={scene.startFrame}                    // 起始帧
          durationInFrames={scene.durationFrames}   // 持续帧数
        >
          {/* 叠化过渡包装 — 第一个场景有淡入，最后一个有淡出，中间有交叉淡入淡出 */}
          <CrossDissolveWrapper
            hasPrev={index > 0}                      // 是否有前一个场景（决定是否淡入）
            hasNext={index < scenes.length - 1}      // 是否有后一个场景（决定是否淡出）
            dissolveFrames={15}                      // 叠化过渡帧数
          >
            <SceneRenderer scene={scene} />
          </CrossDissolveWrapper>
        </Sequence>
      ))}
    </>
  );
};
