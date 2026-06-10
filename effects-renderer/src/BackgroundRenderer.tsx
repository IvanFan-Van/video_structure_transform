"use client";

import { AbsoluteFill, Img, OffthreadVideo } from "remotion";
import { cn } from "#lib/utils";
import type { Background } from "./types/composition";

interface BackgroundRendererProps {
  background: Background;
  className?: string;
}

const FIT_MAP: Record<string, React.CSSProperties["objectFit"]> = {
  cover: "cover",
  contain: "contain",
  fill: "fill",
};

export function BackgroundRenderer({
  background,
  className,
}: BackgroundRendererProps) {
  switch (background.type) {
    case "solid":
      return (
        <AbsoluteFill
          className={cn(className)}
          style={{ backgroundColor: background.color }}
        />
      );

    case "gradient": {
      const angle = background.angle ?? 180;
      const stops = background.colors
        .map(
          (c: string, i: number) =>
            `${c} ${(i / (background.colors.length - 1)) * 100}%`,
        )
        .join(", ");
      return (
        <AbsoluteFill
          className={cn(className)}
          style={{
            background: `linear-gradient(${angle}deg, ${stops})`,
          }}
        />
      );
    }

    case "video":
      return (
        <AbsoluteFill className={cn(className)}>
          <OffthreadVideo
            src={background.src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: FIT_MAP[background.fit ?? "cover"] ?? "cover",
            }}
            volume={background.volume ?? 0}
            startFrom={
              background.trimStart !== undefined
                ? Math.round(background.trimStart * 30)
                : undefined
            }
            endAt={
              background.trimStart !== undefined &&
              background.trimDuration !== undefined
                ? Math.round(
                    (background.trimStart + background.trimDuration) * 30,
                  )
                : undefined
            }
          />
        </AbsoluteFill>
      );

    case "image":
      return (
        <AbsoluteFill className={cn(className)}>
          <Img
            src={background.src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: FIT_MAP[background.fit ?? "cover"] ?? "cover",
            }}
          />
        </AbsoluteFill>
      );

    case "effect": {
      const { EFFECT_REGISTRY } = require("./effects") as {
        EFFECT_REGISTRY: Record<
          string,
          { component: React.ComponentType<any> }
        >;
      };
      const meta = EFFECT_REGISTRY[background.effectId];
      if (!meta) {
        return (
          <AbsoluteFill
            className={cn(className)}
            style={{ backgroundColor: "#0a0a0a" }}
          />
        );
      }
      const EffectComponent = meta.component;
      return (
        <AbsoluteFill className={cn(className)}>
          <EffectComponent {...(background.effectProps ?? {})} />
        </AbsoluteFill>
      );
    }

    case "none":
    default:
      return null;
  }
}
