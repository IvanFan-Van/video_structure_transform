import { useMemo } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { BaseNode } from '../ui/BaseNode';
import { sliderStyle, fmtF } from '../../utils';

interface Props { x: number; y: number; onPosChange: (id: string, x: number, y: number, w: number, h: number) => void; }

const FIELDS = [
  { key: 'n_embd', label: 'embedding dim', min: 4, max: 128, step: 4 },
  { key: 'n_head', label: 'attention heads', min: 1, max: 16, step: 1 },
  { key: 'n_layer', label: 'layers', min: 1, max: 8, step: 1 },
  { key: 'block_size', label: 'context window', min: 4, max: 64, step: 4 },
  { key: 'num_steps', label: 'training steps', min: 50, max: 3000, step: 50 },
  { key: 'learning_rate', label: 'learning rate', min: 0.001, max: 0.05, step: 0.001 },
];

export function ArchitectureNode({ x, y, onPosChange }: Props) {
  const dataset = useAppStore((s) => s.dataset);
  const config = useAppStore((s) => s.config);
  const training = useAppStore((s) => s.training);
  const setConfig = useAppStore((s) => s.setConfig);

  const paramCount = useMemo(() => {
    const { n_embd, n_layer, block_size } = config;
    const v = dataset?.vocabSize || 28;
    return v * n_embd + block_size * n_embd + v * n_embd +
      n_layer * (4 * n_embd * n_embd + 4 * n_embd * n_embd + n_embd * 4 * n_embd + n_embd * 4 * n_embd);
  }, [config, dataset]);

  const flopsPerStep = paramCount * config.block_size * 2;

  return (
    <BaseNode x={x} y={y} w={300} title="Architecture" active={!!dataset} accent="#f59e0b" id="config" onPosChange={onPosChange}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {FIELDS.map(({ key, label, min, max, step }) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '9px', color: '#999', minWidth: '85px' }}>{label}</span>
            <input type="range" min={min} max={max} step={step} value={config[key]} disabled={training}
              onChange={(e) => setConfig(c => ({ ...c, [key]: parseFloat(e.target.value) }))} style={sliderStyle} />
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#333', minWidth: '36px', textAlign: 'right' }}>
              {key === 'learning_rate' ? config[key].toFixed(3) : config[key]}
            </span>
          </div>
        ))}
        <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '6px', display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#999' }}>
          <span>params: <span style={{ fontWeight: 700, color: '#333' }}>{paramCount.toLocaleString()}</span></span>
          <span>{fmtF(flopsPerStep)} FLOPs/step</span>
        </div>
      </div>
    </BaseNode>
  );
}
