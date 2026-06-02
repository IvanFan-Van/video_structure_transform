import { useAppStore } from '../../store/useAppStore';
import { BaseNode } from '../ui/BaseNode';
import { sliderStyle } from '../../utils';

const PROMPT_PRESETS = ['', 'ka', 'em', 'ch', 'j', 'al'];

interface Props { x: number; y: number; onPosChange: (id: string, x: number, y: number, w: number, h: number) => void; }

export function GenerateNode({ x, y, onPosChange }: Props) {
  const modelReady = useAppStore((s) => s.modelReady);
  const genPrompt = useAppStore((s) => s.genPrompt);
  const genTemp = useAppStore((s) => s.genTemp);
  const genResults = useAppStore((s) => s.genResults);
  const generating = useAppStore((s) => s.generating);
  const finalSamples = useAppStore((s) => s.finalSamples);
  const setGenPrompt = useAppStore((s) => s.setGenPrompt);
  const setGenTemp = useAppStore((s) => s.setGenTemp);
  const doGenerate = useAppStore((s) => s.doGenerate);

  const handleQuickGenerate = (pr: string) => {
    setGenPrompt(pr);
    setTimeout(doGenerate, 50);
  };

  return (
    <BaseNode x={x} y={y} w={310} title="Generate" active={modelReady} accent="#06b6d4" id="generate" onPosChange={onPosChange}>
      {modelReady ? <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          <input type="text" value={genPrompt} onChange={(e) => setGenPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && doGenerate()}
            placeholder="type a beginning..."
            style={{ flex: 1, padding: '6px 8px', fontSize: '11px', fontFamily: 'inherit', border: '1px solid #e0e0e0', borderRadius: '3px', outline: 'none', color: '#333' }} />
          <button onClick={doGenerate} disabled={generating} style={{
            padding: '6px 10px', fontSize: '10px', fontWeight: 600, fontFamily: 'inherit',
            background: '#333', color: '#fff', border: 'none', borderRadius: '3px', cursor: 'pointer',
          }}>{generating ? '...' : '→'}</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9px', color: '#999' }}>
          <span>temp</span>
          <input type="range" min="0.1" max="1.5" step="0.1" value={genTemp}
            onChange={(e) => setGenTemp(parseFloat(e.target.value))} style={sliderStyle} />
          <span style={{ fontWeight: 600, color: '#333' }}>{genTemp.toFixed(1)}</span>
        </div>
        {genResults.length === 0 && <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
          {PROMPT_PRESETS.map((pr) => (
            <button key={pr} onClick={() => handleQuickGenerate(pr)}
              style={{ padding: '3px 6px', fontSize: '8px', fontFamily: 'inherit', background: '#f5f5f5', border: '1px solid #e8e8e8', borderRadius: '2px', color: '#888', cursor: 'pointer' }}>
              {pr ? '"' + pr + '..."' : 'random'}
            </button>
          ))}
        </div>}
        {genResults.length > 0 && <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {genResults.map((s, i) => (
            <div key={i} style={{
              padding: '4px 6px', fontSize: '11px',
              background: i === 0 ? '#f0f7ff' : '#f8f8f8', borderRadius: '2px', color: '#333',
              fontWeight: i === 0 ? 600 : 400, border: i === 0 ? '1px solid #dbeafe' : '1px solid transparent',
            }}>
              {genPrompt && <span style={{ color: '#2563eb' }}>{genPrompt}</span>}
              <span>{s.startsWith(genPrompt) ? s.slice(genPrompt.length) : s}</span>
            </div>
          ))}
        </div>}
        {genResults.length === 0 && finalSamples.length > 0 && <div>
          <div style={{ fontSize: '8px', color: '#bbb', letterSpacing: '1px', marginBottom: '4px' }}>TRAINING SAMPLES</div>
          <div style={{ fontSize: '10px', color: '#666', lineHeight: '18px' }}>{finalSamples.slice(0, 6).join(' · ')}</div>
        </div>}
      </div> : <div style={{ color: '#ddd', fontStyle: 'italic' }}>waiting for model...</div>}
    </BaseNode>
  );
}
