"use client";

import { Img, OffthreadVideo, Sequence } from "remotion";
import { useEffect, useState } from "react";
import type { Overlay } from "./types/composition";

interface OverlayRendererProps {
  overlay: Overlay;
}

type PosStyle = {
  position: "absolute";
  left?: number | string;
  right?: number;
  top?: number | string;
  bottom?: number;
};

function resolvePosition(
  pos: Overlay["position"],
  ow: number,
  oh: number,
): PosStyle {
  const style: PosStyle = { position: "absolute" };

  if (pos.x === "left") style.left = 0;
  else if (pos.x === "right") style.right = 0;
  else if (pos.x === "center") {
    style.left = `calc(50% - ${ow / 2}px)`;
  } else {
    style.left = pos.x;
  }

  if (pos.y === "top") style.top = 0;
  else if (pos.y === "bottom") style.bottom = 0;
  else if (pos.y === "center") {
    style.top = `calc(50% - ${oh / 2}px)`;
  } else {
    style.top = pos.y;
  }

  return style;
}

const FIT_MAP: Record<string, React.CSSProperties["objectFit"]> = {
  cover: "cover",
  contain: "contain",
  fill: "fill",
};

export function OverlayRenderer({ overlay }: OverlayRendererProps) {
  const w = overlay.width ?? 300;
  const h = overlay.height ?? 100;

  const posStyle = resolvePosition(overlay.position, w, h);

  const transforms: string[] = [];
  if (overlay.rotation) transforms.push(`rotate(${overlay.rotation}deg)`);
  if (overlay.scale) transforms.push(`scale(${overlay.scale})`);

  const wrapperStyle: React.CSSProperties = {
    ...posStyle,
    width: w,
    height: h,
    opacity: overlay.opacity ?? 1,
    transform: transforms.length > 0 ? transforms.join(" ") : undefined,
    transformOrigin: "center center",
    willChange: transforms.length > 0 ? "transform" : undefined,
    zIndex: overlay.zIndex,
  };

  return (
    <Sequence
      from={overlay.startFrame}
      durationInFrames={overlay.durationInFrames}
      layout="none"
    >
      <div style={wrapperStyle}>
        {overlay.type === "effect" && (
          <EffectOverlayInner overlay={overlay} />
        )}
        {overlay.type === "image" && (
          <Img
            src={overlay.src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: FIT_MAP[overlay.fit ?? "contain"] ?? "contain",
            }}
          />
        )}
        {overlay.type === "video" && (
          <OffthreadVideo
            src={overlay.src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: FIT_MAP[overlay.fit ?? "contain"] ?? "contain",
            }}
            volume={overlay.volume ?? 0}
            startFrom={
              overlay.trimStart !== undefined
                ? Math.round(overlay.trimStart * 30)
                : undefined
            }
            endAt={
              overlay.trimStart !== undefined &&
              overlay.trimDuration !== undefined
                ? Math.round(
                    (overlay.trimStart + overlay.trimDuration) * 30,
                  )
                : undefined
            }
          />
        )}
      </div>
    </Sequence>
  );
}

function EffectOverlayInner({
  overlay,
}: {
  overlay: Overlay & { type: "effect" };
}) {
  const [EffectComponent, setEffectComponent] =
    useState<React.ComponentType<any> | null>(null);

  useEffect(() => {
    const { EFFECT_REGISTRY } = require("./effects") as {
      EFFECT_REGISTRY: Record<
        string,
        { component: React.ComponentType<any> }
      >;
    };
    const meta = EFFECT_REGISTRY[overlay.effectId];
    if (meta) {
      setEffectComponent(() => meta.component);
    }
  }, [overlay.effectId]);

  if (!EffectComponent) {
    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#999",
          fontSize: 14,
        }}
      />
    );
  }

  return <EffectComponent {...overlay.effectProps} />;
}
