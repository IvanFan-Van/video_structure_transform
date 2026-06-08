/**
 * REMOCN_REGISTRY — 59个remocn视觉组件注册表
 *
 * 作用: 将所有 remocn 组件名映射到 React 组件类，供 RemocnScene.tsx 动态查找和渲染。
 *
 * 设计模式:
 *   1. 每个 remocn 组件在一个独立的 .tsx 文件中实现
 *   2. 注册表 import 所有组件，以组件名为 key 构建字典
 *   3. RemocnScene 通过 REMOCN_REGISTRY[name] 动态查找组件
 *   4. 找不到 → console.warn + 跳过（不会中断渲染）
 *
 * 组件分类:
 *   文字特效:   Typewriter, BlurReveal, StaggeredFadeUp, TrackingIn, ShimmerSweep, RGBGlitchText 等
 *   UI模拟:     CursorFlow, BrowserFlow, TerminalSimulator, ToastNotification 等
 *   代码工具:   GlassCodeBlock, CodeAccordion, CodeDiffWipe, LiveCodeCompilation 等
 *   数据可视化: AnimatedLineChart, AnimatedBarChart, DashboardPopulate 等
 *   过渡转场:   DirectionalWipe, SwipeTransitionWipe, SpatialPush, FrostedGlassWipe 等
 *   产品展示:   HeroDeviceAssemble, DeviceMockupZoom, ProductLaunchTrailer 等
 *   背景装饰:   MeshGradientBg, DynamicGrid, InfiniteBentoPan, StaggeredBentoGrid 等
 *   AI主题:     AIGenerateOverlay, AIGenerationCanvas, FocusZoom, PulsingIndicator 等
 */
import { AIGenerateOverlay } from "./ai-generate-overlay";
import { AIGenerationCanvas } from "./ai-generation-canvas";
import { AnimatedBarChart } from "./animated-bar-chart";
import { AnimatedLineChart } from "./animated-line-chart";
import { BlurReveal } from "./blur-reveal";
import { BoundingBoxSelector } from "./bounding-box-selector";
import { BrowserFlow } from "./browser-flow";
import { BrushStrokeSimulator } from "./brush-stroke-simulator";
import { ChangelogBite } from "./changelog-bite";
import { ChatToPreviewLayout } from "./chat-to-preview-layout";
import { ChromaticAberrationWipe } from "./chromatic-aberration-wipe";
import { CodeAccordion } from "./code-accordion";
import { CodeDiffWipe } from "./code-diff-wipe";
import { CursorFlow } from "./cursor-flow";
import { DashboardPopulate } from "./dashboard-populate";
import { DeviceMockupZoom } from "./device-mockup-zoom";
import { DirectionalWipe } from "./directional-wipe";
import { DragAndDropFlow } from "./drag-and-drop-flow";
import { DynamicGrid } from "./dynamic-grid";
import { EcosystemConstellation } from "./ecosystem-constellation";
import { FocusZoom } from "./focus-zoom";
import { FrostedGlassWipe } from "./frosted-glass-wipe";
import { GlassCodeBlock } from "./glass-code-block";
import { GridPixelateWipe } from "./grid-pixelate-wipe";
import { HeroDeviceAssemble } from "./hero-device-assemble";
import { ImageExpandToFullscreen } from "./image-expand-to-fullscreen";
import { InfiniteBentoPan } from "./infinite-bento-pan";
import { InfiniteMarquee } from "./infinite-marquee";
import { InlineHighlight } from "./inline-highlight";
import { LiveCodeCompilation } from "./live-code-compilation";
import { MarkerHighlight } from "./marker-highlight";
import { MaskedSlideReveal } from "./masked-slide-reveal";
import { MatrixDecode } from "./matrix-decode";
import { MeshGradientBg } from "./mesh-gradient-bg";
import { MorphingModal } from "./morphing-modal";
import { PerspectiveMarquee } from "./perspective-marquee";
import { PipelineJourney } from "./pipeline-journey";
import { PricingTierFocus } from "./pricing-tier-focus";
import { ProductLaunchTrailer } from "./product-launch-trailer";
import { PulsingIndicator } from "./pulsing-indicator";
import { RGBGlitchText } from "./rgb-glitch-text";
import { ShimmerSweep } from "./shimmer-sweep";
import { SlotMachineRoll } from "./slot-machine-roll";
import { SpatialPush } from "./spatial-push";
import { SpotlightCard } from "./spotlight-card";
import { SpringPopIn } from "./spring-pop-in";
import { StaggeredBentoGrid } from "./staggered-bento-grid";
import { StaggeredFadeUp } from "./staggered-fade-up";
import { SuccessConfetti } from "./success-confetti";
import { SwipeTransitionWipe } from "./swipe-transition-wipe";
import { TerminalSimulator } from "./terminal-simulator";
import { TerminalToBrowserDeploy } from "./terminal-to-browser-deploy";
import { TextFadeReplace } from "./text-fade-replace";
import { ToastNotification } from "./toast-notification";
import { ToolMenuSlideIn } from "./tool-menu-slide-in";
import { TrackingIn } from "./tracking-in";
import { Typewriter } from "./typewriter";
import { VisualDocsSnippet } from "./visual-docs-snippet";
import { ZoomThroughTransition } from "./zoom-through-transition";
import type { ComponentType } from "react";

/**
 * 组件注册表 — 组件名 → React 组件类的映射
 *
 * RemocnScene 通过 REMOCN_REGISTRY[effect.component] 动态查找组件。
 * 如果组件名不在注册表中，渲染时会跳过（console.warn + null）。
 *
 * 组件名必须与 transfer.py 中的 _VALID_REMOCN_COMPONENTS 白名单以及
 * remocn_components.json 中的 name 字段保持一致。
 */
export const REMOCN_REGISTRY: Record<string, ComponentType<any>> = {
  AIGenerateOverlay,
  AIGenerationCanvas,
  AnimatedBarChart,
  AnimatedLineChart,
  BlurReveal,
  BoundingBoxSelector,
  BrowserFlow,
  BrushStrokeSimulator,
  ChangelogBite,
  ChatToPreviewLayout,
  ChromaticAberrationWipe,
  CodeAccordion,
  CodeDiffWipe,
  CursorFlow,
  DashboardPopulate,
  DeviceMockupZoom,
  DirectionalWipe,
  DragAndDropFlow,
  DynamicGrid,
  EcosystemConstellation,
  FocusZoom,
  FrostedGlassWipe,
  GlassCodeBlock,
  GridPixelateWipe,
  HeroDeviceAssemble,
  ImageExpandToFullscreen,
  InfiniteBentoPan,
  InfiniteMarquee,
  InlineHighlight,
  LiveCodeCompilation,
  MarkerHighlight,
  MaskedSlideReveal,
  MatrixDecode,
  MeshGradientBg,
  MorphingModal,
  PerspectiveMarquee,
  PipelineJourney,
  PricingTierFocus,
  ProductLaunchTrailer,
  PulsingIndicator,
  RGBGlitchText,
  ShimmerSweep,
  SlotMachineRoll,
  SpatialPush,
  SpotlightCard,
  SpringPopIn,
  StaggeredBentoGrid,
  StaggeredFadeUp,
  SuccessConfetti,
  SwipeTransitionWipe,
  TerminalSimulator,
  TerminalToBrowserDeploy,
  TextFadeReplace,
  ToastNotification,
  ToolMenuSlideIn,
  TrackingIn,
  Typewriter,
  VisualDocsSnippet,
  ZoomThroughTransition,
};
