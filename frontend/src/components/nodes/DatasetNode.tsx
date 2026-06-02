import { useAppStore } from '../../store/useAppStore';
import { PRESETS } from '../../constants';
import { BaseNode } from '../ui/BaseNode';

interface Props {
  x: number;
  y: number;
  onPosChange: (id: string, x: number, y: number, w: number, h: number) => void;
}

export function DatasetNode({ x, y, onPosChange }: Props) {
  const dataset = useAppStore((s) => s.dataset);
  const selectedPreset = useAppStore((s) => s.selectedPreset);
  const loadPreset = useAppStore((s) => s.loadPreset);
  const loadCustomDataset = useAppStore((s) => s.loadCustomDataset);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer?.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      loadCustomDataset(ev.target?.result as string);
    };
    reader.readAsText(file);
  };

  return (
    <BaseNode x={x} y={y} w={280} title="Dataset" active={!!dataset} accent="#2563eb" id="dataset" onPosChange={onPosChange}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <select value={selectedPreset} onChange={(e) => loadPreset(e.target.value)}
          style={{ padding: '6px 8px', fontSize: '11px', fontFamily: 'inherit', border: '1px solid #e0e0e0', borderRadius: '3px', background: '#fafafa', color: '#555', cursor: 'pointer', outline: 'none' }}>
          <option value="">choose dataset...</option>
          {Object.entries(PRESETS).map(([k, v]) => <option key={k} value={k}>{v.label} — {v.desc}</option>)}
        </select>
        <input type="file" accept=".txt,.csv" id="fileUpload" style={{ display: 'none' }}
          onChange={(e) => {
            const file = e.target.files?.[0]; if (!file) return;
            const reader = new FileReader();
            reader.onload = (ev) => loadCustomDataset(ev.target?.result as string);
            reader.readAsText(file);
          }} />
        <div
          onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = '#999'; }}
          onDragLeave={(e) => { e.currentTarget.style.borderColor = '#d4d4d4'; }}
          onDrop={handleFileDrop}
          onClick={() => document.getElementById('fileUpload')?.click()}
          style={{ border: '1.5px dashed #d4d4d4', borderRadius: '3px', padding: '14px', textAlign: 'center', color: '#bbb', fontSize: '10px', cursor: 'pointer' }}>
          drop or click to upload .txt<div style={{ fontSize: '8px', color: '#ddd', marginTop: '3px' }}>one entry per line</div>
        </div>
        {dataset && <div style={{ fontSize: '10px', color: '#888', lineHeight: '16px' }}>
          <span style={{ color: '#333', fontWeight: 600 }}>{dataset.numDocs.toLocaleString()}</span> entries · vocab <span style={{ color: '#333', fontWeight: 600 }}>{dataset.vocabSize}</span> chars
          <div style={{ marginTop: '4px', color: '#bbb', fontSize: '9px' }}>{dataset.sampleDocs.slice(0, 6).join(', ')}...</div>
        </div>}
      </div>
    </BaseNode>
  );
}
