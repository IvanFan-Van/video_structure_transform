export function OnsetChart({ data, height = 40 }: { data: number[]; height?: number }) {
  if (!data.length) return null;
  const mx = Math.max(...data) || 1;
  const barW = Math.max(0.6, 90 / data.length);

  return (
    <svg viewBox={`0 0 ${data.length > 0 ? data.length : 1} 100`} preserveAspectRatio="none" style={{ width: "100%", height, display: "block" }}>
      {data.map((v, i) => (
        <rect
          key={i}
          x={i}
          y={100 - (v / mx) * 90}
          width={barW}
          height={Math.max(0.5, (v / mx) * 90)}
          fill="#c4b5fd"
        />
      ))}
    </svg>
  );
}
