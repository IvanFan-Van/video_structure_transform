function centroidToColor(v: number, mn: number, mx: number): string {
  if (mx === mn) return "#7c3aed";
  const t = (v - mn) / (mx - mn);
  const hue = 270 - t * 230;
  return `hsl(${Math.round(hue)}, 70%, 55%)`;
}

export function CentroidChart({ data, height = 50 }: { data: number[]; height?: number }) {
  if (!data.length) return null;
  const mx = Math.max(...data) || 1;
  const mn = Math.min(...data);
  const rng = mx - mn || 1;
  const toY = (v: number) => 92 - ((v - mn) / rng) * 80;
  const toX = (i: number) => (i / Math.max(data.length - 1, 1)) * 100;

  const segments: { x1: number; y1: number; x2: number; y2: number; color: string }[] = [];
  for (let i = 0; i < data.length - 1; i++) {
    segments.push({
      x1: toX(i), y1: toY(data[i]),
      x2: toX(i + 1), y2: toY(data[i + 1]),
      color: centroidToColor((data[i] + data[i + 1]) / 2, mn, mx),
    });
  }
  if (segments.length === 0 && data.length === 1) {
    const x = toX(0), y = toY(data[0]);
    segments.push({ x1: x, y1: y, x2: x, y2: y, color: centroidToColor(data[0], mn, mx) });
  }

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height, display: "block" }}>
      {segments.map((seg, i) => (
        <line key={i} x1={seg.x1} y1={seg.y1} x2={seg.x2} y2={seg.y2} stroke={seg.color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      ))}
      {data.length > 1 && (
        <circle cx={toX(data.length - 1)} cy={toY(data[data.length - 1])} r="2" fill={centroidToColor(data[data.length - 1], mn, mx)} vectorEffect="non-scaling-stroke" />
      )}
    </svg>
  );
}
