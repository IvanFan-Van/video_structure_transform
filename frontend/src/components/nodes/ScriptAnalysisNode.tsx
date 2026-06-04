import { useState } from 'react';
import { useVideoStore } from '../../store/useVideoStore';
import { BaseNode } from '../ui/BaseNode';
import { TranscriptResult, TranscriptStage } from '../../store/types';

interface Props {
  x: number;
  y: number;
  onPosChange: (id: string, x: number, y: number, w: number, h: number) => void;
}

const STAGE_LABELS: Record<string, string> = {
  hook: 'Hook',
  setup: 'Setup',
  story: 'Story',
  insight: 'Insight',
  cta: 'CTA',
  outro: 'Outro',
};

export function ScriptAnalysisNode({ x, y, onPosChange }: Props) {
  const transcriptResult = useVideoStore((s) => s.transcriptResult);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const stages: { key: string; label: string; data: TranscriptStage }[] = [];
  if (transcriptResult) {
    for (const key of Object.keys(STAGE_LABELS)) {
      const data = transcriptResult[key as keyof TranscriptResult];
      if (data) {
        stages.push({ key, label: STAGE_LABELS[key], data });
      }
    }
  }

  const toggle = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <BaseNode
      x={x} y={y} w={300}
      title="Script Analysis"
      active={!!transcriptResult}
      accent="#8b5cf6"
      id="script_analysis"
      onPosChange={onPosChange}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {!transcriptResult && (
          <div
            style={{
              fontSize: '9px',
              color: '#bbb',
              textAlign: 'center',
              padding: '12px 0',
            }}
          >
            Waiting for extraction...
          </div>
        )}

        {transcriptResult && (
          <>
            <div
              style={{
                fontSize: '10px',
                fontWeight: 600,
                color: '#8b5cf6',
                letterSpacing: '2px',
                textAlign: 'center',
                marginBottom: '2px',
              }}
            >
              ✓ ANALYZED
            </div>
            {stages.map(({ key, label, data }) => {
              const open = expanded[key] ?? false;
              return (
                <div key={key}>
                  <div
                    onClick={() => toggle(key)}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '6px 8px',
                      borderRadius: '3px',
                      background: open ? '#f5f3ff' : '#fafafa',
                      border: open ? '1px solid #e9d5ff' : '1px solid #f0f0f0',
                      cursor: 'pointer',
                      transition: 'background 0.15s, border-color 0.15s',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '8px', color: open ? '#8b5cf6' : '#bbb' }}>
                        {open ? '▼' : '▶'}
                      </span>
                      <span
                        style={{
                          fontSize: '9px',
                          fontWeight: 600,
                          color: open ? '#6d28d9' : '#555',
                        }}
                      >
                        {label}
                      </span>
                    </div>
                    <span style={{ fontSize: '8px', color: '#bbb' }}>
                      {data.start_time.toFixed(1)}s — {data.end_time.toFixed(1)}s
                    </span>
                  </div>
                  {open && (
                    <div
                      style={{
                        marginTop: '4px',
                        padding: '8px',
                        background: '#fafafa',
                        borderRadius: '3px',
                        border: '1px solid #f0f0f0',
                        fontSize: '8px',
                        color: '#555',
                        lineHeight: '1.6',
                      }}
                    >
                      <div style={{ marginBottom: '6px' }}>
                        <div
                          style={{
                            fontSize: '7px',
                            fontWeight: 600,
                            letterSpacing: '1px',
                            color: '#bbb',
                            marginBottom: '3px',
                          }}
                        >
                          VISUAL TEXT
                        </div>
                        <div style={{ color: '#333', whiteSpace: 'pre-wrap' }}>
                          {data.visual_text || '(empty)'}
                        </div>
                      </div>
                      <div>
                        <div
                          style={{
                            fontSize: '7px',
                            fontWeight: 600,
                            letterSpacing: '1px',
                            color: '#bbb',
                            marginBottom: '3px',
                          }}
                        >
                          AUDIO TEXT
                        </div>
                        <div style={{ color: '#333', whiteSpace: 'pre-wrap' }}>
                          {data.audio_text || '(empty)'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </>
        )}
      </div>
    </BaseNode>
  );
}
