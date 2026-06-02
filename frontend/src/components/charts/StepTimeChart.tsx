export function StepTimeChart({ data, height = 35 }: { data: number[], height?: number }) {
  if (!data.length) return null;
  const mx = Math.max(...data, 1);
  return (
    <svg viewBox={'0 0 ' + data.length + ' 100'} preserveAspectRatio="none" style={{ width: '100%', height, display: 'block' }}>
      {data.map((v, i) => <rect key={i} x={i} y={100 - (v / mx) * 90} width="0.8" height={(v / mx) * 90} fill="#dbeafe" />)}
    </svg>
  );
}
