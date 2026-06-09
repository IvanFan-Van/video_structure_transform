// src/effects/index.ts
// ============= Typography =============
import { BlurReveal } from "#components/remocn/blur-reveal";
import { StaggeredFadeUp } from "#components/remocn/staggered-fade-up";
import { MaskedSlideReveal } from "#components/remocn/masked-slide-reveal";
import { TrackingIn } from "#components/remocn/tracking-in";
import { InlineHighlight } from "#components/remocn/inline-highlight";
import { MarkerHighlight } from "#components/remocn/marker-highlight";
import { ShimmerSweep } from "#components/remocn/shimmer-sweep";
import { Typewriter } from "#components/remocn/typewriter";
import { TextFadeReplace } from "#components/remocn/text-fade-replace";
import { SlotMachineRoll } from "#components/remocn/slot-machine-roll";
import { InfiniteMarquee } from "#components/remocn/infinite-marquee";
import { PerspectiveMarquee } from "#components/remocn/perspective-marquee";
import { MatrixDecode } from "#components/remocn/matrix-decode";
import { RGBGlitchText } from "#components/remocn/rgb-glitch-text";

// ============= Core Primitives =============
import { SpringPopIn } from "#components/remocn/spring-pop-in";
import { PulsingIndicator } from "#components/remocn/pulsing-indicator";
import { SuccessConfetti } from "#components/remocn/success-confetti";
import { CursorFlow } from "#components/remocn/cursor-flow";
import { BrushStrokeSimulator } from "#components/remocn/brush-stroke-simulator";
import { BoundingBoxSelector } from "#components/remocn/bounding-box-selector";
import { ToastNotification } from "#components/remocn/toast-notification";

// ============= Environment & Lighting =============
import { MeshGradientBg } from "#components/remocn/mesh-gradient-bg";
import { DynamicGrid } from "#components/remocn/dynamic-grid";
import { SpotlightCard } from "#components/remocn/spotlight-card";

// ============= UI Blocks =============
import { GlassCodeBlock } from "#components/remocn/glass-code-block";
import { TerminalSimulator } from "#components/remocn/terminal-simulator";
import { CodeAccordion } from "#components/remocn/code-accordion";
import { CodeDiffWipe } from "#components/remocn/code-diff-wipe";
import { StaggeredBentoGrid } from "#components/remocn/staggered-bento-grid";
import { ChatToPreviewLayout } from "#components/remocn/chat-to-preview-layout";
import { AIGenerateOverlay } from "#components/remocn/ai-generate-overlay";
import { ToolMenuSlideIn } from "#components/remocn/tool-menu-slide-in";
import { AnimatedLineChart } from "#components/remocn/animated-line-chart";
import { AnimatedBarChart } from "#components/remocn/animated-bar-chart";
import { DragAndDropFlow } from "#components/remocn/drag-and-drop-flow";

// ============= Transitions =============
import { ZoomThroughTransition } from "#components/remocn/zoom-through-transition";
import { DeviceMockupZoom } from "#components/remocn/device-mockup-zoom";
import { MorphingModal } from "#components/remocn/morphing-modal";
import { ImageExpandToFullscreen } from "#components/remocn/image-expand-to-fullscreen";
import { DirectionalWipe } from "#components/remocn/directional-wipe";
import { SwipeTransitionWipe } from "#components/remocn/swipe-transition-wipe";
import { SpatialPush } from "#components/remocn/spatial-push";
import { FrostedGlassWipe } from "#components/remocn/frosted-glass-wipe";
import { GridPixelateWipe } from "#components/remocn/grid-pixelate-wipe";
import { ChromaticAberrationWipe } from "#components/remocn/chromatic-aberration-wipe";

// ============= Compositions =============
import { HeroDeviceAssemble } from "#components/remocn/hero-device-assemble";
import { EcosystemConstellation } from "#components/remocn/ecosystem-constellation";
import { InfiniteBentoPan } from "#components/remocn/infinite-bento-pan";
import { BrowserFlow } from "#components/remocn/browser-flow";
import { AIGenerationCanvas } from "#components/remocn/ai-generation-canvas";
import { LiveCodeCompilation } from "#components/remocn/live-code-compilation";
import { TerminalToBrowserDeploy } from "#components/remocn/terminal-to-browser-deploy";
import { DashboardPopulate } from "#components/remocn/dashboard-populate";
import { PipelineJourney } from "#components/remocn/pipeline-journey";
import { PricingTierFocus } from "#components/remocn/pricing-tier-focus";
import { ProductLaunchTrailer } from "#components/remocn/product-launch-trailer";
import { ChangelogBite } from "#components/remocn/changelog-bite";
import { VisualDocsSnippet } from "#components/remocn/visual-docs-snippet";

import type { FC } from "react";

export interface EffectProps {
	[key: string]: unknown;
}

export interface EffectMeta {
	component: FC<any>;
	defaultDurationInFrames: number;
	defaultFps: number;
	defaultWidth: number;
	defaultHeight: number;
}

const DEFAULT_FPS = 30;
const DEFAULT_WIDTH = 1920;
const DEFAULT_HEIGHT = 1080;

function meta(durationInFrames: number): Pick<EffectMeta, "defaultFps" | "defaultWidth" | "defaultHeight" | "defaultDurationInFrames"> {
	return {
		defaultDurationInFrames: durationInFrames,
		defaultFps: DEFAULT_FPS,
		defaultWidth: DEFAULT_WIDTH,
		defaultHeight: DEFAULT_HEIGHT,
	};
}

export const EFFECT_REGISTRY: Record<string, EffectMeta> = {
	// ============= Typography (90 frames / 3s) =============
	"blur-reveal": { component: BlurReveal, ...meta(90) },
	"staggered-fade-up": { component: StaggeredFadeUp, ...meta(90) },
	"masked-slide-reveal": { component: MaskedSlideReveal, ...meta(90) },
	"tracking-in": { component: TrackingIn, ...meta(90) },
	"inline-highlight": { component: InlineHighlight, ...meta(90) },
	"marker-highlight": { component: MarkerHighlight, ...meta(90) },
	"shimmer-sweep": { component: ShimmerSweep, ...meta(90) },
	typewriter: { component: Typewriter, ...meta(90) },
	"text-fade-replace": { component: TextFadeReplace, ...meta(90) },
	"slot-machine-roll": { component: SlotMachineRoll, ...meta(90) },
	"infinite-marquee": { component: InfiniteMarquee, ...meta(90) },
	"perspective-marquee": { component: PerspectiveMarquee, ...meta(90) },
	"matrix-decode": { component: MatrixDecode, ...meta(90) },
	"rgb-glitch-text": { component: RGBGlitchText, ...meta(90) },

	// ============= Core Primitives (120 frames / 4s) =============
	"spring-pop-in": { component: SpringPopIn, ...meta(120) },
	"pulsing-indicator": { component: PulsingIndicator, ...meta(120) },
	"success-confetti": { component: SuccessConfetti, ...meta(120) },
	"cursor-flow": { component: CursorFlow, ...meta(120) },
	"brush-stroke-simulator": { component: BrushStrokeSimulator, ...meta(120) },
	"bounding-box-selector": { component: BoundingBoxSelector, ...meta(120) },
	"toast-notification": { component: ToastNotification, ...meta(120) },

	// ============= Environment & Lighting (120 frames / 4s) =============
	"mesh-gradient-bg": { component: MeshGradientBg, ...meta(120) },
	"dynamic-grid": { component: DynamicGrid, ...meta(120) },
	"spotlight-card": { component: SpotlightCard, ...meta(120) },

	// ============= UI Blocks (150 frames / 5s) =============
	"glass-code-block": { component: GlassCodeBlock, ...meta(150) },
	"terminal-simulator": { component: TerminalSimulator, ...meta(150) },
	"code-accordion": { component: CodeAccordion, ...meta(150) },
	"code-diff-wipe": { component: CodeDiffWipe, ...meta(150) },
	"staggered-bento-grid": { component: StaggeredBentoGrid, ...meta(150) },
	"chat-to-preview-layout": { component: ChatToPreviewLayout, ...meta(150) },
	"ai-generate-overlay": { component: AIGenerateOverlay, ...meta(150) },
	"tool-menu-slide-in": { component: ToolMenuSlideIn, ...meta(150) },
	"animated-line-chart": { component: AnimatedLineChart, ...meta(150) },
	"animated-bar-chart": { component: AnimatedBarChart, ...meta(150) },
	"drag-and-drop-flow": { component: DragAndDropFlow, ...meta(150) },

	// ============= Transitions (60 frames / 2s) =============
	"zoom-through-transition": { component: ZoomThroughTransition, ...meta(60) },
	"device-mockup-zoom": { component: DeviceMockupZoom, ...meta(60) },
	"morphing-modal": { component: MorphingModal, ...meta(60) },
	"image-expand-to-fullscreen": { component: ImageExpandToFullscreen, ...meta(60) },
	"directional-wipe": { component: DirectionalWipe, ...meta(60) },
	"swipe-transition-wipe": { component: SwipeTransitionWipe, ...meta(60) },
	"spatial-push": { component: SpatialPush, ...meta(60) },
	"frosted-glass-wipe": { component: FrostedGlassWipe, ...meta(60) },
	"grid-pixelate-wipe": { component: GridPixelateWipe, ...meta(60) },
	"chromatic-aberration-wipe": { component: ChromaticAberrationWipe, ...meta(60) },

	// ============= Compositions (300 frames / 10s) =============
	"hero-device-assemble": { component: HeroDeviceAssemble, ...meta(300) },
	"ecosystem-constellation": { component: EcosystemConstellation, ...meta(300) },
	"infinite-bento-pan": { component: InfiniteBentoPan, ...meta(300) },
	"browser-flow": { component: BrowserFlow, ...meta(300) },
	"ai-generation-canvas": { component: AIGenerationCanvas, ...meta(300) },
	"live-code-compilation": { component: LiveCodeCompilation, ...meta(300) },
	"terminal-to-browser-deploy": { component: TerminalToBrowserDeploy, ...meta(300) },
	"dashboard-populate": { component: DashboardPopulate, ...meta(300) },
	"pipeline-journey": { component: PipelineJourney, ...meta(300) },
	"pricing-tier-focus": { component: PricingTierFocus, ...meta(300) },
	"product-launch-trailer": { component: ProductLaunchTrailer, ...meta(300) },
	"changelog-bite": { component: ChangelogBite, ...meta(300) },
	"visual-docs-snippet": { component: VisualDocsSnippet, ...meta(300) },
};
