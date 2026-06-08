/**
 * Root 组件 — Remotion Composition 定义
 *
 * 作用: 定义视频渲染的基本参数（分辨率、帧率、时长）和默认 props。
 *
 * 运行模式:
 *   remotion studio src/index.ts  → 在浏览器中预览（使用 defaultProps）
 *   remotion render ... --props=xxx.json → 渲染正式视频（使用传入的 props）
 *
 * defaultProps 仅用于开发预览，正式渲染时通过 --props 传入 transfer 生成的 JSON。
 */
import React from 'react';
import { Composition } from 'remotion';
import { VideoComposition } from './VideoComposition';
import { RemotionProps } from './types';

// 开发预览用默认 props — 直接从 remotion_props.json 复制粘贴后修改
// 正式渲染时通过 --props 参数覆盖
const defaultProps: RemotionProps = {
  fps: 30,                                    // 帧率（固定30fps）
  durationInFrames: 498,                      // 总帧数
  width: 1080,                                // 画面宽度（9:16竖屏标准）
  height: 1920,                               // 画面高度（9:16竖屏标准）
  scenes: [
    {
      id: 'hook',
      slot_id: 1,
      startFrame: 0,                          // 该场景起始帧号
      durationFrames: 90,                     // 该场景持续帧数
      type: 'text_overlay',                   // 渲染类型: text_overlay/emphasis_text/remocn_composed
      text: '我家孩子把这个坚果饼干分享给身边小伙伴吃啊',
      textStyle: {
        fontSize: 64,
        color: '#FFFFFF',
        fontWeight: 'bold',
        animation: 'typewriter',              // 文字动画类型
        position_x: 50,                       // 水平位置%（中心=50）
        position_y: 50,                       // 垂直位置%（中心=50，底部=82）
      },
      visualHint: '',
      emotion: 'curious',
      beatFrames: [4, 20, 36, 52, 65, 81],   // 该场景内的BGM卡点相对帧号
      hasMaterial: false,
      backgroundVideo: null,
      backgroundImage: null,
      backgroundColorFallback: '#0D0D0D',    // 无素材时的纯色背景
      requiredElements: [],
      gapFilled: true,
      gapStrategy: 'color_bg+text',
      fill_method: 'color_bg',
    },
    {
      id: 'testimonial',
      slot_id: 2,
      startFrame: 90,
      durationFrames: 75,
      type: 'text_overlay',
      text: '没想到身边全圈层的宝妈都来找我要这个长野坚果芙的链接',
      textStyle: {
        fontSize: 64,
        color: '#FFD700',
        fontWeight: 'bold',
        animation: 'bounce',
        position_x: 50,
        position_y: 50,
      },
      visualHint: '',
      emotion: 'excited',
      beatFrames: [7, 22, 39, 55, 70],
      hasMaterial: false,
      backgroundVideo: null,
      backgroundImage: null,
      backgroundColorFallback: '#0D0D0D',
      requiredElements: [],
      gapFilled: true,
      gapStrategy: 'color_bg+text',
      fill_method: 'color_bg',
    },
    {
      id: 'product_show',
      slot_id: 3,
      startFrame: 165,
      durationFrames: 240,
      type: 'emphasis_text',                  // KenBurns + 卡点脉冲渲染模式
      text: '打开袋子就闻到浓浓的蛋香味，每一片都做得又酥又脆，吃起来口感极佳，蛋香混合着坚果香，一口下去超满足',
      textStyle: {
        fontSize: 64,
        color: '#F0F0F0',
        fontWeight: 'bold',
        animation: 'fade_in',
        position_x: 50,
        position_y: 50,
      },
      visualHint: '',
      emotion: 'sincere',
      beatFrames: [10, 24, 41, 56, 72, 88, 103, 121, 142, 159, 176, 193, 210, 225],
      hasMaterial: false,
      backgroundVideo: null,
      backgroundImage: null,
      backgroundColorFallback: '#1A1A2E',
      requiredElements: [],
      gapFilled: true,
      gapStrategy: 'color_bg+text',
      fill_method: 'color_bg',
    },
    {
      id: 'outro',
      slot_id: 4,
      startFrame: 405,
      durationFrames: 93,
      type: 'emphasis_text',
      text: '抖音 × 今日头条 来平台 关注热点事件 坚果有哪些营养价值？',
      textStyle: {
        fontSize: 64,
        color: '#FFFFFF',
        fontWeight: 'bold',
        animation: 'fade_in',
        position_x: 50,
        position_y: 50,
      },
      visualHint: '',
      emotion: 'neutral',
      beatFrames: [2, 18, 35],
      hasMaterial: false,
      backgroundVideo: null,
      backgroundImage: null,
      backgroundColorFallback: '#111111',
      requiredElements: [],
      gapFilled: true,
      gapStrategy: 'color_bg+text',
      fill_method: 'color_bg',
    },
  ],
  bgmPath: '',
  voiceoverPath: '',
  voiceoverText: '',
  rhythmPattern: 'steady_build',
  visualStyle: 'product_centric',
  gapReport: [],
  migrationSummary: {} as any,
};

export const Root: React.FC = () => {
  return (
    <Composition
      id="VideoComposition"                  // 组合ID（render 命令中指定）
      component={VideoComposition as any}    // 渲染组件
      durationInFrames={498}                 // 默认时长
      fps={30}                               // 默认帧率
      width={1080}
      height={1920}
      defaultProps={defaultProps}            // 默认 props（dev 模式用）
    />
  );
};
