// src/DynamicRenderer.tsx
import { EFFECT_REGISTRY, EffectProps } from "./effects";

interface DynamicRendererProps {
  effectId?: string;
  effectProps?: EffectProps;
}

export const DynamicRenderer: React.FC<DynamicRendererProps> = ({
  effectId,
  effectProps = {},
}) => {
  const meta = effectId ? EFFECT_REGISTRY[effectId] : undefined;

  if (!meta) {
    // 未知特效时渲染红色错误帧，不崩溃
    return (
      <div style={{ background: "red", color: "white", padding: 40 }}>
        Unknown effect: {effectId}
      </div>
    );
  }

  const { component: EffectComponent } = meta;
  return <EffectComponent {...effectProps} />;
};
