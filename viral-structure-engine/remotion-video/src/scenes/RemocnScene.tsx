/**
 * RemocnScene — remocn 59个视觉组件渲染场景
 *
 * 与其他场景的最大区别: 不使用 AnimatedText 组件，而是直接渲染
 * remocn 组件库中的注册组件（如 Typewriter、BlurReveal、SpringPopIn等）。
 *
 * 渲染架构:
 *   1. 按标点拆句 → 每句分配独立 Sequence
 *   2. 每个 Sentence 按 startFrame 进入时间线（替换模式）
 *   3. 句子通过 renderEffect() 递归渲染 remocn 组件树:
 *      - 叶组件直接渲染（如 Typewriter）
 *      - 容器组件支持 children 嵌套（如 SpringPopIn > BlurReveal）
 *
 * 组件查找:
 *   从 REMOCN_REGISTRY (registry.ts) 中动态查找组件名 → React组件类
 *   找不到 → console.warn + 返回 null（不会中断渲染）
 *
 * 位置偏移:
 *   remocn 组件内部默认居中(50%, 50%)
 *   → 通过 translateY(yOffset) 偏移到 textStyle.position_y 目标位置
 *   → yOffset = position_y - 50（如 82-50=32% 向下偏移）
 *
 * props 动态解析:
 *   支持特殊值 "__fn:回调函数代码" → 运行时 eval 为真实函数
 *   用于传递动画回调（如 onComplete）
 */
import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { SceneData, RemocnEffect } from "../types";
import { SceneBackground } from "../components/SceneBackground";
import { REMOCN_REGISTRY } from "../components/remocn/registry";

/**
 * 递归渲染 remocn 组件树
 *
 * @param effect       当前组件的描述
 * @param index        组件在兄弟列表中的索引（React key）
 * @param overrideText 覆盖组件 props 中的 text 字段（用于注入当前句子文本）
 * @returns React节点
 */
function renderEffect(
  effect: RemocnEffect,
  index: number,
  overrideText?: string,
): React.ReactNode {
  // 从注册表中查找组件
  const C = REMOCN_REGISTRY[effect.component];
  if (!C) {
    console.warn(`Remocn component "${effect.component}" not found in registry`);
    return null;
  }

  // 解析 props（处理 __fn: 特殊值）
  const resolvedProps = resolveProps(effect.props);

  // 如果指定了 overrideText，覆盖 props.text
  if (overrideText !== undefined) {
    resolvedProps.text = overrideText;
  }

  // 容器组件: 有 children 时用 React.createElement 传递子节点
  if (effect.children && effect.children.length > 0) {
    return React.createElement(
      C,
      { key: index, ...resolvedProps },
      ...effect.children.map((child, i) => renderEffect(child, i, overrideText)),
    );
  }

  // 叶组件: 直接渲染
  return React.createElement(C, { key: index, ...resolvedProps });
}

/**
 * 解析 props 中的特殊值
 *
 * 如果某个 prop 的值以 "__fn:" 开头，则将其后的内容动态 eval 为 JavaScript 函数。
 * 用于传递动画回调函数（JSON 中无法直接存储函数）。
 *
 * 例: "__fn:() => console.log('done')" → 真实的可调用函数
 */
function resolveProps(props: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(props)) {
    if (typeof v === "string" && v.startsWith("__fn:")) {
      try {
        out[k] = new Function(`return ${v.slice(5)}`)();  // 移除 "__fn:" 前缀后 eval
      } catch {
        out[k] = v;  // 解析失败 → 保留原值
      }
    } else {
      out[k] = v;
    }
  }
  return out;
}

/**
 * RemocnScene 主组件
 *
 * 渲染流程:
 *   1. 检查有无 remocnEffects（空 → 只渲染背景）
 *   2. 如果只有1句 → 不拆Sequence，直接全量渲染
 *   3. 多句 → 每句一个 Sequence + 替换模式
 */
export const RemocnScene: React.FC<SceneData> = ({
  text,                     // 完整文案
  textStyle,                // 文字样式（用于位置偏移）
  backgroundVideo,
  backgroundImage,
  remocnEffects,            // remocn 组件列表
  backgroundColorFallback,
  durationFrames,           // 场景持续帧数（用于分配每句帧数）
}) => {
  // 按标点拆句
  const sentences = text.split(/[，。！？,!?]/).filter(Boolean);

  // 空文案 → 只渲染背景色
  if (sentences.length === 0) {
    return (
      <AbsoluteFill
        style={{ backgroundColor: backgroundColorFallback || "#000000" }}
      />
    );
  }

  // 每句分配的帧数
  const framesPerSentence = Math.max(
    Math.floor(durationFrames / sentences.length),
    8,
  );

  // 无 remocn 组件 → 只渲染背景（理论不会发生，由 transfer 保证至少有一个组件）
  if (!remocnEffects || remocnEffects.length === 0) {
    return (
      <AbsoluteFill style={{ position: "relative" }}>
        <SceneBackground
          backgroundVideo={backgroundVideo}
          backgroundImage={backgroundImage}
          backgroundColorFallback={backgroundColorFallback || "#000000"}
        />
      </AbsoluteFill>
    );
  }

  // 计算垂直偏移量（remocn 组件默认居中50%，需要偏移到目标位置）
  // 如 textStyle.position_y=82 → yOffset=32 → 向下偏移32%
  const yOffset = textStyle.position_y - 50;

  return (
    <AbsoluteFill style={{ position: "relative" }}>
      {/* 三级背景 */}
      <SceneBackground
        backgroundVideo={backgroundVideo}
        backgroundImage={backgroundImage}
        backgroundColorFallback={backgroundColorFallback || "#000000"}
      />
      {/* 逐句 Sequence — 替换模式 */}
      {sentences.map((sentence, i) => (
        <Sequence
          key={i}
          from={i * framesPerSentence}          // 该句出现的起始帧
          durationInFrames={framesPerSentence}   // 该句持续帧数
        >
          <div
            style={{
              width: "100%",
              height: "100%",
              position: "relative",
              transform: `translateY(${yOffset}%)`,  // 垂直偏移到目标位置
            }}
          >
            {remocnEffects.map((effect, j) =>
              renderEffect(effect, j, sentence),  // 递归渲染组件树
            )}
          </div>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
