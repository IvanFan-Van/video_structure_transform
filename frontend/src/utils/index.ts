export const fmt = (ms: number) => ms < 1000 ? ms + 'ms' : (ms / 1000).toFixed(1) + 's';

export const fmtF = (f: number) => {
  if (f > 1e9) return (f / 1e9).toFixed(1) + 'G';
  if (f > 1e6) return (f / 1e6).toFixed(1) + 'M';
  if (f > 1e3) return (f / 1e3).toFixed(0) + 'K';
  return String(f);
};

export const sliderStyle = { flex: 1, accentColor: '#999', cursor: 'pointer', height: '2px' };

export const fmtSize = (bytes: number | null): string => {
  if (bytes === null) return '—';
  if (bytes > 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
  if (bytes > 1e6) return (bytes / 1e6).toFixed(1) + ' MB';
  if (bytes > 1e3) return (bytes / 1e3).toFixed(0) + ' KB';
  return bytes + ' B';
};
