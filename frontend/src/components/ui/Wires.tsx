import { Pos } from '../../store/types';

interface WiresProps {
  positions: Record<string, Pos>;
  wires: [string, string][];
  tick: number;
}

export function Wires({ positions, wires, tick }: WiresProps) {
  void tick;
  return (
    <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 5 }}>
      {wires.map(([from, to], i) => {
        const a = positions[from], b = positions[to];
        if (!a || !b) return null;
        // Smart connection: pick closest edges
        const aCx = a.x + a.w / 2, aCy = a.y + a.h / 2;
        const bCx = b.x + b.w / 2, bCy = b.y + b.h / 2;
        // Determine which edges to connect
        let x1 = 0, y1 = 0, x2 = 0, y2 = 0;
        const dx = bCx - aCx, dy = bCy - aCy;
        if (Math.abs(dx) > Math.abs(dy)) {
          // Horizontal connection
          if (dx > 0) { x1 = a.x + a.w; y1 = aCy; x2 = b.x; y2 = bCy; }
          else { x1 = a.x; y1 = aCy; x2 = b.x + b.w; y2 = bCy; }
        } else {
          // Vertical connection
          if (dy > 0) { x1 = aCx; y1 = a.y + a.h; x2 = bCx; y2 = b.y; }
          else { x1 = aCx; y1 = a.y; x2 = bCx; y2 = b.y + b.h; }
        }
        const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
        let d;
        if (Math.abs(dx) > Math.abs(dy)) {
          d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
        } else {
          d = `M ${x1} ${y1} C ${x1} ${my}, ${x2} ${my}, ${x2} ${y2}`;
        }
        return (
          <g key={i}>
            <path d={d} fill="none" stroke="#d4d4d4" strokeWidth="1.5" strokeDasharray="6,4" />
            <circle cx={x2} cy={y2} r="3" fill="#d4d4d4" />
            <circle cx={x1} cy={y1} r="2.5" fill="none" stroke="#d4d4d4" strokeWidth="1" />
          </g>
        );
      })}
    </svg>
  );
}
