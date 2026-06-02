import { useAppStore } from '../../store/useAppStore';
import { BaseNode } from '../ui/BaseNode';

interface Props { x: number; y: number; onPosChange: (id: string, x: number, y: number, w: number, h: number) => void; }

export function TokenizerNode({ x, y, onPosChange }: Props) {
  const dataset = useAppStore((s) => s.dataset);
  return (
    <BaseNode x={x} y={y} w={280} title="Tokenizer" active={!!dataset} accent="#8b5cf6" id="tokenizer" onPosChange={onPosChange}>
      {dataset ? <div style={{ color: '#888', lineHeight: '16px' }}>
        <div style={{ marginBottom: '6px' }}>character-level · vocab <span style={{ fontWeight: 700, color: '#333' }}>{dataset.vocabSize}</span></div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px', marginBottom: '6px' }}>
          {['BOS', ...dataset.chars].slice(0, 30).map((ch, i) => {
            const display = ch === ' ' ? '␣' : ch === '\t' ? '⇥' : ch === "'" ? "'" : ch || '?';
            return <span key={i} style={{ padding: '1px 4px', fontSize: '8px', background: i < 1 ? '#fef3c7' : '#f5f5f5', border: '1px solid ' + (i < 1 ? '#fde68a' : '#e8e8e8'), borderRadius: '2px', color: i < 1 ? '#92400e' : '#888', fontWeight: i < 1 ? 600 : 400, minWidth: '14px', textAlign: 'center', display: 'inline-block' }}>{display}</span>;
          })}
        </div>
        <div style={{ fontSize: '9px', color: '#bbb' }}>&quot;{dataset.sampleDocs[0]}&quot; → [BOS, {dataset.sampleDocs[0]?.split('').join(', ')}, BOS]</div>
      </div> : <div style={{ color: '#ddd', fontStyle: 'italic' }}>waiting for dataset...</div>}
    </BaseNode>
  );
}
