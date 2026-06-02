import { useMemo } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { BaseNode } from '../ui/BaseNode';
import { StepTimeChart } from '../charts/StepTimeChart';
import { fmt, fmtF } from '../../utils';

interface Props { x: number; y: number; onPosChange: (id: string, x: number, y: number, w: number, h: number) => void; }

export function MetricsNode({ x, y, onPosChange }: Props) {
  const lossHistory = useAppStore((s) => s.lossHistory);
  const stepTimes = useAppStore((s) => s.stepTimes);
  const currentLoss = useAppStore((s) => s.currentLoss);
  const currentStep = useAppStore((s) => s.currentStep);
  const totalTime = useAppStore((s) => s.totalTime);
  const config = useAppStore((s) => s.config);
  const dataset = useAppStore((s) => s.dataset);
  const runHistory = useAppStore((s) => s.runHistory);

  const paramCount = useMemo(() => {
    const { n_embd, n_layer, block_size } = config;
    const v = dataset?.vocabSize || 28;
    return v * n_embd + block_size * n_embd + v * n_embd +
      n_layer * (4 * n_embd * n_embd + 4 * n_embd * n_embd + n_embd * 4 * n_embd + n_embd * 4 * n_embd);
  }, [config, dataset]);

  const flopsPerStep = paramCount * config.block_size * 2;
  const totalFlops = flopsPerStep * currentStep;

  return (
    <BaseNode x={x} y={y} w={310} title="Metrics" active={lossHistory.length > 0} accent="#ec4899" id="metrics" onPosChange={onPosChange}>
      {lossHistory.length > 0 ? <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '10px' }}>
          {[
            { label: 'LOSS', value: currentLoss.toFixed(4) },
            { label: 'PERPLEXITY', value: Math.exp(currentLoss).toFixed(1) },
            { label: 'TOTAL FLOPS', value: fmtF(totalFlops) },
            { label: 'THROUGHPUT', value: (stepTimes.length && stepTimes[stepTimes.length - 1] > 0) ? fmtF(Math.round(flopsPerStep / (stepTimes[stepTimes.length - 1] / 1000))) + '/s' : '—' },
          ].map(({ label, value }) => (
            <div key={label} style={{ background: '#f8f8f8', borderRadius: '3px', padding: '5px 7px' }}>
              <div style={{ fontSize: '7px', color: '#bbb', letterSpacing: '1px' }}>{label}</div>
              <div style={{ fontWeight: 700, color: '#333' }}>{value}</div>
            </div>
          ))}
        </div>
        <div>
          <div style={{ fontSize: '8px', color: '#bbb', letterSpacing: '1px', marginBottom: '2px' }}>STEP TIME (ms)</div>
          <StepTimeChart data={stepTimes.slice(-100)} height={35} />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '8px', color: '#ccc', marginTop: '2px' }}>
            <span>avg {stepTimes.length ? Math.round(stepTimes.reduce((a, b) => a + b, 0) / stepTimes.length) : 0}ms</span>
            <span>total {fmt(totalTime)}</span>
          </div>
        </div>
        <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '6px', fontSize: '8px', color: '#bbb', lineHeight: '14px' }}>
          <div>your GPT: <span style={{ color: '#555' }}>{paramCount.toLocaleString()} params · {fmtF(totalFlops)} FLOPs</span></div>
          <div>GPT-4 est: <span style={{ color: '#555' }}>~1.8T params · ~10²⁵ FLOPs</span></div>
        </div>
        {runHistory.length > 0 && <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '4px' }}>
          <div style={{ fontSize: '8px', color: '#bbb', letterSpacing: '1px', marginBottom: '3px' }}>SAVED RUNS</div>
          {runHistory.map((run, i) => (
            <div key={run.id} style={{ fontSize: '9px', color: '#888', padding: '2px 0', display: 'flex', justifyContent: 'space-between' }}>
              <span>#{i + 1} {run.config.n_layer}L/{run.config.n_embd}d</span>
              <span style={{ color: '#555' }}>loss {run.finalLoss.toFixed(3)} · {fmt(run.totalTime)}</span>
            </div>
          ))}
        </div>}
      </div> : <div style={{ color: '#ddd', fontStyle: 'italic' }}>waiting for training...</div>}
    </BaseNode>
  );
}
