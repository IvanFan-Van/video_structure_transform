import React from 'react';
import { useVideoStore } from '../../store/useVideoStore';
import { BaseNode } from '../ui/BaseNode';
import { Tooltip } from '../ui/Tooltip';
import { sliderStyle } from '../../utils';

interface Props { x: number; y: number; onPosChange: (id: string, x: number, y: number, w: number, h: number) => void; }

function Row({ label, tip, children }: { label: string; tip?: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <Tooltip tip={tip ?? ''} inline>
        <span style={{ fontSize: '9px', color: tip ? '#555' : '#999', minWidth: '80px', cursor: tip ? 'help' : undefined, borderBottom: tip ? '1px dotted #ccc' : undefined }}>{label}</span>
      </Tooltip>
      {children}
    </div>
  );
}

function Val({ children }: { children: React.ReactNode }) {
  return <span style={{ fontSize: '11px', fontWeight: 600, color: '#333', minWidth: '28px', textAlign: 'right' }}>{children}</span>;
}

const selectStyle = { padding: '4px 6px', fontSize: '11px', fontFamily: 'inherit', border: '1px solid #e0e0e0', borderRadius: '3px', background: '#fafafa', color: '#555', outline: 'none', flex: 1 } as const;
const inputTextStyle = { flex: 1, padding: '4px 6px', fontSize: '11px', fontFamily: 'inherit', border: '1px solid #e0e0e0', borderRadius: '3px', background: '#fafafa', color: '#555', outline: 'none' } as const;

export function CompressConfigNode({ x, y, onPosChange }: Props) {
  const uploadResult = useVideoStore((s) => s.uploadResult);
  const compressConfig = useVideoStore((s) => s.compressConfig);
  const setCompressConfig = useVideoStore((s) => s.setCompressConfig);
  const hasTargetBitrate = compressConfig.target_v_bitrate !== null;

  return (
    <BaseNode x={x} y={y} w={300} title="Compress Config" active={!!uploadResult} accent="#14b8a6" id="compress_config" tourId="compress_config" onPosChange={onPosChange}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <Row label="vcodec" tip="视频编码器。libx264 兼容性最好；libx265 压缩率更高但编码速度较慢">
          <select value={compressConfig.vcodec} onChange={(e) => setCompressConfig({ ...compressConfig, vcodec: e.target.value })}
            style={selectStyle}>
            <option value="libx264">libx264</option>
            <option value="libx265">libx265</option>
          </select>
        </Row>
        <Row label="crf" tip="恒定质量因子，0=无损 23=默认 51=最差。值越小质量越高、文件越大。设置 target bitrate 后此项失效">
          <input type="range" min={0} max={51} step={1} value={compressConfig.crf ?? 32}
            disabled={hasTargetBitrate}
            onChange={(e) => setCompressConfig({ ...compressConfig, crf: parseInt(e.target.value), target_v_bitrate: null })} style={sliderStyle} />
          <Val>{hasTargetBitrate ? '—' : compressConfig.crf}</Val>
        </Row>
        <Row label="target bitrate" tip="目标视频比特率（如 2M、500k）。设置后 CRF 模式失效，编码器以此比特率为目标">
          <input type="text" value={compressConfig.target_v_bitrate ?? ''}
            placeholder="e.g. 2M"
            onChange={(e) => setCompressConfig({ ...compressConfig, target_v_bitrate: e.target.value || null, crf: e.target.value ? null : compressConfig.crf })}
            style={inputTextStyle} />
        </Row>
        <Row label="scale width" tip="缩放目标宽度（像素），高度按比例自动计算。留空保持原始分辨率">
          <input type="number" value={compressConfig.scale_width ?? ''}
            placeholder="original"
            onChange={(e) => setCompressConfig({ ...compressConfig, scale_width: e.target.value ? parseInt(e.target.value) : null })}
            style={inputTextStyle} />
        </Row>
        <Row label="max fps" tip="最大帧率限制。留空保持原始帧率">
          <input type="number" value={compressConfig.max_fps ?? ''}
            placeholder="original"
            onChange={(e) => setCompressConfig({ ...compressConfig, max_fps: e.target.value ? parseInt(e.target.value) : null })}
            style={inputTextStyle} />
        </Row>
        <Row label="acodec" tip="音频编码器。aac 通用兼容性好；libmp3lame 输出 MP3 格式">
          <select value={compressConfig.acodec} onChange={(e) => setCompressConfig({ ...compressConfig, acodec: e.target.value })}
            style={selectStyle}>
            <option value="aac">aac</option>
            <option value="libmp3lame">libmp3lame</option>
          </select>
        </Row>
        <Row label="audio bitrate" tip="音频比特率（如 128k、192k）。值越高音质越好、文件越大">
          <input type="text" value={compressConfig.target_a_bitrate}
            onChange={(e) => setCompressConfig({ ...compressConfig, target_a_bitrate: e.target.value })}
            style={inputTextStyle} />
        </Row>
        {uploadResult && (
          <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '6px', fontSize: '9px', color: '#999' }}>
            source: <span style={{ fontWeight: 600, color: '#333' }}>{uploadResult.asset_id.slice(0, 12)}...</span>
            <span style={{ color: '#bbb' }}> ({uploadResult.metadata.width}×{uploadResult.metadata.height})</span>
          </div>
        )}
      </div>
    </BaseNode>
  );
}
