/**
 * AnimatedText — 5种文字动画 + BGM卡点发光
 *
 * 支持的动画类型:
 *   typewriter: 逐字显示 + 闪烁光标（从视频片段提取的字幕动画）
 *   fade_in:    整体淡入（透明度0→1，20帧内）
 *   bounce:     Spring弹性弹入（0.5→1缩放，阻尼100/刚度200）
 *   slide_in:   从下向上滑入（80px偏移，阻尼12/质量0.5）
 *   glitch:     RGB三色通道分离 + 水平/垂直抖动（sin波驱动，入场后衰减）
 *
 * BGM卡点发光:
 *   相对帧离最近卡点 ≤2帧 → 白色文字发光（textShadow），强度随距离衰减。
 *
 * remotion 动画原理:
 *   useCurrentFrame() 返回当前帧号（随时间递增）
 *   interpolate() 将帧号映射到目标值（如透明度0→1）
 *   spring() 生成模拟物理弹簧的缓动曲线
 */
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

interface AnimatedTextProps {
  text: string;             // 要显示的文字
  animation: string;        // 动画类型
  color: string;            // 文字颜色(hex)
  fontSize: number;         // 字体大小(px)
  fontWeight: string;       // 字重
  beatFrames?: number[];    // BGM卡点相对帧号（用于卡点发光效果）
}

export const AnimatedText: React.FC<AnimatedTextProps> = ({
  text,
  animation,
  color,
  fontSize,
  fontWeight,
  beatFrames = [],
}) => {
  const frame = useCurrentFrame();      // 当前帧号
  const { fps } = useVideoConfig();     // 帧率

  /**
   * typewriter: 逐字显示
   * 每字约占2帧，最少30帧显示完整句子。
   */
  const getVisibleText = () => {
    if (animation !== 'typewriter') return text;
    const totalFrames = Math.max(text.length * 2, 30);  // 总显示帧数
    const visibleCount = Math.floor(
      interpolate(frame, [0, totalFrames], [0, text.length], {
        extrapolateRight: 'clamp',
      })
    );
    return text.slice(0, visibleCount);  // 截取已显示部分
  };

  /**
   * fade_in: 整体淡入
   * 20帧内从0→1
   */
  const opacity = (() => {
    if (animation === 'fade_in') {
      return interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
    }
    return 1;
  })();

  /**
   * bounce: Spring弹性弹入
   * 物理参数: damping=100(阻尼), stiffness=200(刚度)
   * → 弹性回弹效果，从0.5倍缩放弹入
   */
  const scale = (() => {
    if (animation === 'bounce') {
      return spring({
        frame,
        fps,
        from: 0.5,   // 起始缩放
        to: 1,       // 目标缩放
        config: { damping: 100, stiffness: 200 },
      });
    }
    return 1;
  })();

  /**
   * slide_in: 从下方滑入
   * 物理参数: damping=12, mass=0.5 → 带质量感的平滑滑动
   */
  const translateY = (() => {
    if (animation === 'slide_in') {
      return spring({
        frame,
        fps,
        from: 80,    // 起始偏移(px)
        to: 0,       // 目标位置
        config: { damping: 12, mass: 0.5 },
      });
    }
    return 0;
  })();

  /**
   * BGM卡点发光: 找到最近卡点帧，距离≤2帧时发光
   * 发光的textShadow强度随距离衰减: 距离0→glow=0.6, 距离2→glow=0
   */
  const getBeatGlow = () => {
    if (beatFrames.length === 0) return 0;
    // 找到最近的卡点帧
    const nearest = beatFrames.reduce((prev, curr) =>
      Math.abs(curr - frame) < Math.abs(prev - frame) ? curr : prev
    );
    const dist = Math.abs(nearest - frame);
    if (dist <= 2) return interpolate(dist, [0, 2], [0.6, 0]);  // 距离越小越亮
    return 0;
  };

  /**
   * glitch: RGB三色通道分离特效
   * 效果: 入场后持续20帧的RGB通道水平/垂直抖动，随后10帧衰减消失
   *
   * 实现:
   *   - cyan层(#00FFFF): 水平+垂直偏移 → mixBlendMode: screen
   *   - magenta层(#FF00FF): 反向水平+垂直偏移 → mixBlendMode: screen
   *   - 基底层: 文字本体
   * 三色通道分离在外围会形成类似"重影"的视觉故障效果
   */
  if (animation === 'glitch') {
    const glitchDuration = 20;    // 故障效果持续时间(帧)
    const decayFrames = 10;      // 衰减时间(帧)
    // raw: 故障强度（1→0衰减）
    const raw = 1 - interpolate(frame, [glitchDuration, glitchDuration + decayFrames], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    // 用 sin 波生成伪随机的水平/垂直偏移
    const offsetX = Math.sin(frame / 5) * 5 * raw;
    const offsetY = Math.sin(frame / 10) * 10 * raw;

    return (
      <div
        style={{
          position: 'relative',
          fontFamily: 'PingFang SC, Noto Sans SC, Microsoft YaHei, sans-serif',
          textAlign: 'center',
          lineHeight: 1.6,
          padding: '0 64px',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          letterSpacing: '0.02em',
          color,
          fontSize,
          fontWeight,
        }}
      >
        {/* cyan 偏移层 — 青蓝色通道水平+垂直偏移 */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            color: '#00FFFF',
            transform: `translate(${offsetX}px, ${offsetY}px)`,
            mixBlendMode: 'screen',  // 与底层混合产生彩色重影
            fontSize,
            fontWeight,
            fontFamily: 'inherit',
            textAlign: 'center',
            lineHeight: 1.6,
            padding: '0 64px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            letterSpacing: '0.02em',
          }}
        >
          {text}
        </div>
        {/* magenta 偏移层 — 品红色通道反向偏移 */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            color: '#FF00FF',
            transform: `translate(${-offsetX}px, ${-offsetY}px)`,
            mixBlendMode: 'screen',
            fontSize,
            fontWeight,
            fontFamily: 'inherit',
            textAlign: 'center',
            lineHeight: 1.6,
            padding: '0 64px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            letterSpacing: '0.02em',
          }}
        >
          {text}
        </div>
        {/* 基底层 — 本体文字 */}
        <div style={{ opacity: raw > 0 ? 0.85 : 1 }}>{text}</div>
      </div>
    );
  }

  // 卡点发光值
  const glow = getBeatGlow();
  // 打字机动画显示的文字
  const displayText = getVisibleText();

  return (
    <div
      style={{
        opacity,                            // 淡入效果
        transform: `translateY(${translateY}px) scale(${scale})`,  // 滑入+弹入
        color,
        fontSize,
        fontWeight,
        fontFamily: 'PingFang SC, Noto Sans SC, Microsoft YaHei, sans-serif',
        textAlign: 'center',
        lineHeight: 1.6,
        padding: '0 64px',
        // BGM卡点发光: textShadow 随 glow 值增强
        textShadow:
          glow > 0
            ? `0 0 ${glow * 30}px rgba(255,255,255,${glow}), 0 0 ${glow * 60}px rgba(255,255,255,${glow * 0.5})`
            : 'none',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        letterSpacing: '0.02em',
      }}
    >
      {displayText}
      {/* typewriter 闪烁光标: 每8帧闪烁一次（on-off交替） */}
      {animation === 'typewriter' && displayText.length < text.length && (
        <span
          style={{
            opacity: Math.floor(frame / 8) % 2 === 0 ? 1 : 0,  // 每8帧切换可见/不可见
            color,
          }}
        >
          |
        </span>
      )}
    </div>
  );
};
