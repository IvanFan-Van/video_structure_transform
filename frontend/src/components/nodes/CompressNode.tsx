import { useVideoStore } from '../../store/useVideoStore';
import { BaseNode } from '../ui/BaseNode';
import { fmtSize } from '../../utils';

interface Props { x: number; y: number; onPosChange: (id: string, x: number, y: number, w: number, h: number) => void; }

function CompareRow({ label, before, after }: { label: string; before: string; after: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span style={{ color: '#bbb' }}>{label}</span>
      <span><span style={{ color: '#999' }}>{before}</span> → <span style={{ color: '#333', fontWeight: 600 }}>{after}</span></span>
    </div>
  );
}

export function CompressNode({ x, y, onPosChange }: Props) {
  const uploadResult = useVideoStore((s) => s.uploadResult);
  const isCompressing = useVideoStore((s) => s.isCompressing);
  const compressResult = useVideoStore((s) => s.compressResult);
  const startCompress = useVideoStore((s) => s.startCompress);
  const stopCompress = useVideoStore((s) => s.stopCompress);
  const videoErrors = useVideoStore((s) => s.videoErrors);
  const hasError = videoErrors.some((e) => e.nodeId === 'compress');

  const savingsPct = compressResult && uploadResult
    ? Math.round((1 - (compressResult.metadata.size ?? 0) / (uploadResult.metadata.size ?? 1)) * 100)
    : null;

  return (
    <BaseNode x={x} y={y} w={300} title="Compress" active={!!uploadResult || !!compressResult} accent="#06b6d4" error={hasError} id="compress" onPosChange={onPosChange}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {!isCompressing && !compressResult && (
          <button onClick={startCompress} disabled={!uploadResult}
            style={{
              padding: '10px', fontSize: '11px', fontWeight: 600, fontFamily: 'inherit', letterSpacing: '1px',
              background: uploadResult ? '#06b6d4' : '#e8e8e8', color: uploadResult ? '#fff' : '#bbb',
              border: 'none', borderRadius: '3px', cursor: uploadResult ? 'pointer' : 'not-allowed',
            }}>▶ COMPRESS</button>
        )}
        {isCompressing && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
            <div style={{
              fontSize: '10px', fontWeight: 600, color: '#06b6d4', letterSpacing: '1px',
            }}>Compressing...</div>
            <button
              onClick={stopCompress}
              style={{
                padding: '5px', fontSize: '9px', fontFamily: 'inherit',
                background: 'transparent', border: '1px solid #e0e0e0',
                borderRadius: '3px', color: '#999', cursor: 'pointer',
              }}
            >■ STOP</button>
          </div>
        )}
        {compressResult && (
          <>
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#06b6d4', letterSpacing: '2px', textAlign: 'center', marginBottom: '4px' }}>✓ COMPRESSED</div>
            {uploadResult && (
              <div style={{ fontSize: '9px', color: '#888', lineHeight: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0', paddingBottom: '2px', marginBottom: '2px', color: '#bbb', fontSize: '8px', letterSpacing: '1px' }}>
                  <span>Before → After</span>
                </div>
                <CompareRow label="resolution" before={`${uploadResult.metadata.width}×${uploadResult.metadata.height}`} after={`${compressResult.metadata.width}×${compressResult.metadata.height}`} />
                <CompareRow label="size" before={fmtSize(uploadResult.metadata.size)} after={fmtSize(compressResult.metadata.size)} />
                <CompareRow label="fps" before={String(uploadResult.metadata.fps ?? '—')} after={String(compressResult.metadata.fps ?? '—')} />
                <CompareRow label="codec" before={uploadResult.metadata.codec ?? '—'} after={compressResult.metadata.codec ?? '—'} />
                {savingsPct !== null && (
                  <div style={{ textAlign: 'center', marginTop: '4px', fontWeight: 600, fontSize: '10px', color: savingsPct > 0 ? '#22c55e' : '#999' }}>
                    {savingsPct > 0 ? `${savingsPct}% smaller` : 'same size'}
                  </div>
                )}
              </div>
            )}
            <button onClick={startCompress} disabled={isCompressing}
              style={{ padding: '5px 10px', fontSize: '9px', fontFamily: 'inherit', background: 'transparent', border: '1px solid #e0e0e0', borderRadius: '3px', color: '#999', cursor: 'pointer', alignSelf: 'center' }}>
              RECOMPRESS
            </button>
          </>
        )}
      </div>
    </BaseNode>
  );
}
