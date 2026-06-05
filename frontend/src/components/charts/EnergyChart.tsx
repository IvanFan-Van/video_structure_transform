export function EnergyChart({ data, height = 50 }: { data: number[]; height?: number }) {
  if (!data.length) return null;
  const mx = Math.max(...data) || 1;
  const mn = 0;
  const rng = mx - mn;
  const toY = (v: number) => 95 - ((v - mn) / rng) * 80;
  const toX = (i: number) => (i / Math.max(data.length - 1, 1)) * 100;

  const points = data.map((v, i) => `${toX(i)},${toY(v)}`).join(" ");
  const areaPoints = `0,95 ${points} 100,95`;

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height, display: "block" }}>
      <defs>
        <linearGradient id="energyGrad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#7c3aed" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill="url(#energyGrad)" />
      <polyline fill="none" stroke="#7c3aed" strokeWidth="1.2" points={points} vectorEffect="non-scaling-stroke" />
      {data.length > 1 && (
        <circle cx={toX(data.length - 1)} cy={toY(data[data.length - 1])} r="2" fill="#7c3aed" vectorEffect="non-scaling-stroke" />
      )}
    </svg>
  );
}
