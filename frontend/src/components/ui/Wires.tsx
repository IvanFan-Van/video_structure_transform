import { Pos } from "../../store/types";

interface WiresProps {
    positions: Record<string, Pos>;
    wires: [string, string][];
    zoom: number;
    panX: number;
    panY: number;
}

function toScreen(
    lx: number,
    ly: number,
    zoom: number,
    panX: number,
    panY: number,
) {
    return { sx: lx * zoom + panX, sy: ly * zoom + panY };
}

export function Wires({ positions, wires, zoom, panX, panY }: WiresProps) {
    return (
        <svg
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                width: "100vw",
                height: "100vh",
                pointerEvents: "none",
                zIndex: 5,
            }}
        >
            {wires.map(([from, to], i) => {
                const a = positions[from],
                    b = positions[to];
                if (!a || !b) return null;

                // 仍在逻辑空间计算哪条边连接
                const aCx = a.x + a.w / 2,
                    aCy = a.y + a.h / 2;
                const bCx = b.x + b.w / 2,
                    bCy = b.y + b.h / 2;
                const dx = bCx - aCx,
                    dy = bCy - aCy;

                let lx1: number, ly1: number, lx2: number, ly2: number;
                if (Math.abs(dx) > Math.abs(dy)) {
                    if (dx > 0) {
                        lx1 = a.x + a.w;
                        ly1 = aCy;
                        lx2 = b.x;
                        ly2 = bCy;
                    } else {
                        lx1 = a.x;
                        ly1 = aCy;
                        lx2 = b.x + b.w;
                        ly2 = bCy;
                    }
                } else {
                    if (dy > 0) {
                        lx1 = aCx;
                        ly1 = a.y + a.h;
                        lx2 = bCx;
                        ly2 = b.y;
                    } else {
                        lx1 = aCx;
                        ly1 = a.y;
                        lx2 = bCx;
                        ly2 = b.y + b.h;
                    }
                }

                const { sx: x1, sy: y1 } = toScreen(lx1, ly1, zoom, panX, panY);
                const { sx: x2, sy: y2 } = toScreen(lx2, ly2, zoom, panX, panY);

                const mx = (x1 + x2) / 2,
                    my = (y1 + y2) / 2;
                let d;
                if (Math.abs(dx) > Math.abs(dy)) {
                    d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
                } else {
                    d = `M ${x1} ${y1} C ${x1} ${my}, ${x2} ${my}, ${x2} ${y2}`;
                }

                return (
                    <g key={i}>
                        <path
                            d={d}
                            fill="none"
                            stroke="#d4d4d4"
                            strokeWidth={1.5 * zoom}
                            strokeDasharray="6,4"
                        />
                        <circle cx={x2} cy={y2} r={3 * zoom} fill="#d4d4d4" />
                        <circle
                            cx={x1}
                            cy={y1}
                            r={2.5 * zoom}
                            fill="none"
                            stroke="#d4d4d4"
                            strokeWidth="1"
                        />
                    </g>
                );
            })}
        </svg>
    );
}
