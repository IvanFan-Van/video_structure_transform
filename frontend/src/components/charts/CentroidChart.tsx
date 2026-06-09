import { useMemo } from "react";
import { aggregateWindows } from "../../utils/chart";

const WINDOW_COUNT = 100;

function centroidToColor(v: number, mn: number, mx: number): string {
    if (mx === mn) return "#7c3aed";
    const t = (v - mn) / (mx - mn);
    const hue = 270 - t * 230;
    return `hsl(${Math.round(hue)}, 70%, 55%)`;
}

export function CentroidChart({
    data,
    height = 40,
}: {
    data: number[];
    height?: number;
}) {
    const bars = useMemo(() => {
        if (!data.length) return null;
        const down = aggregateWindows(data, WINDOW_COUNT, "avg");
        const mn = Math.min(...down);
        const mx = Math.max(...down) || 1;
        const rng = mx - mn || 1;
        return down.map((v) => {
            const h = Math.max(1, ((v - mn) / rng) * 100);
            return { h, color: centroidToColor(v, mn, mx) };
        });
    }, [data]);

    if (!bars) return null;

    const totalWidth = bars.length;
    const barW = totalWidth > 0 ? Math.min(1, 100 / totalWidth) : 0.5;
    const gap =
        totalWidth > 0
            ? Math.max(0, (100 - barW * totalWidth) / (totalWidth + 1))
            : 0;

    return (
        <svg
            viewBox={`0 0 ${totalWidth} 100`}
            preserveAspectRatio="none"
            style={{ width: "100%", height, display: "block" }}
        >
            {bars.map((b, i) => (
                <rect
                    key={i}
                    x={gap + i * (barW + gap)}
                    y={100 - b.h}
                    width={barW}
                    height={b.h}
                    fill={b.color}
                />
            ))}
        </svg>
    );
}
