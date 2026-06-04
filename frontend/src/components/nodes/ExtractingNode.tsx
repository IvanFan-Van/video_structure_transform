import { useVideoStore } from '../../store/useVideoStore';
import { BaseNode } from '../ui/BaseNode';

interface Props {
  x: number;
  y: number;
  onPosChange: (id: string, x: number, y: number, w: number, h: number) => void;
}

const TODO_ITEMS = [
  { key: 'script', label: 'Analyze Script Structure' },
  { key: 'bgm', label: 'Analyze BGM Features' },
  { key: 'features', label: 'Analyze Video Features' },
] as const;

const STATUS_CONFIG: Record<string, { icon: string; color: string; text: string; blink?: boolean }> = {
  pending: { icon: '○', color: '#ccc', text: 'pending' },
  loading: { icon: '○', color: '#555', text: 'in progress', blink: true },
  done:    { icon: '●', color: '#22c55e', text: 'completed' },
  error:   { icon: '✕', color: '#ef4444', text: 'failed' },
};

export function ExtractingNode({ x, y, onPosChange }: Props) {
  const compressResult = useVideoStore((s) => s.compressResult);
  const isExtractingFlow = useVideoStore((s) => s.isExtractingFlow);
  const scriptStatus = useVideoStore((s) => s.scriptStatus);
  const startExtractScript = useVideoStore((s) => s.startExtractScript);
  const videoErrors = useVideoStore((s) => s.videoErrors);
  const hasError = videoErrors.some((e) => e.nodeId === 'extracting');

  const getStatus = (key: string) => {
    if (key === 'script') return scriptStatus;
    return 'pending';
  };

  return (
    <BaseNode
      x={x} y={y} w={300}
      title="Extracting"
      active={!!compressResult}
      accent="#7c3aed"
      error={hasError}
      id="extracting"
      onPosChange={onPosChange}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {!isExtractingFlow && (
          <button
            onClick={startExtractScript}
            disabled={!compressResult}
            style={{
              padding: '10px',
              fontSize: '11px',
              fontWeight: 600,
              fontFamily: 'inherit',
              letterSpacing: '1px',
              background: compressResult ? '#333' : '#e8e8e8',
              color: compressResult ? '#fff' : '#bbb',
              border: 'none',
              borderRadius: '3px',
              cursor: compressResult ? 'pointer' : 'not-allowed',
            }}
          >
            ▶ START EXTRACTING
          </button>
        )}

        {isExtractingFlow && (
          <style
            dangerouslySetInnerHTML={{
              __html: `
              @keyframes extractPulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
              }
              `,
            }}
          />
        )}

        {isExtractingFlow && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {TODO_ITEMS.map((item) => {
              const status = getStatus(item.key);
              const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
              return (
                <div
                  key={item.key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '9px',
                    padding: '6px 8px',
                    borderRadius: '3px',
                    background: status === 'loading' ? '#fafafa' : 'transparent',
                    border: status === 'loading' ? '1px solid #f0f0f0' : '1px solid transparent',
                  }}
                >
                  <span
                    style={{
                      color: cfg.color,
                      fontSize: '10px',
                      marginRight: '8px',
                      fontWeight: 700,
                      ...(cfg.blink ? { animation: 'extractPulse 1.2s ease-in-out infinite' } : {}),
                    }}
                  >
                    {cfg.icon}
                  </span>
                  <span
                    style={{
                      flex: 1,
                      color: status === 'done' ? '#555' : status === 'error' ? '#ef4444' : status === 'loading' ? '#333' : '#bbb',
                      fontWeight: status === 'loading' ? 600 : 400,
                    }}
                  >
                    {item.label}
                  </span>
                  <span style={{ color: cfg.color, fontSize: '8px' }}>
                    {cfg.text}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </BaseNode>
  );
}
