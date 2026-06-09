import { useMemo } from "react";
import { aggregateWindows, mean } from "../../utils/chart";

const WINDOW_COUNT = 100;

export function FluxChart({
    data,
    height = 30,
}: {
    data: number[];
    height?: number;
}) {
    const { bars, threshold } = useMemo(() => {
        if (!data.length) return { bars: null, threshold: 0 };
        const down = aggregateWindows(data, WINDOW_COUNT, "max");
        const mx = Math.max(...down) || 1;
        const t = mean(down);
        return {
            bars: down.map((v) => {
                const h = Math.max(1, (v / mx) * 100);
                const above = v >= t;
                return { h, above };
            }),
            threshold: (t / mx) * 100,
        };
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
                    fill={b.above ? "#7c3aed" : "#ddd6fe"}
                />
            ))}
            <line
                x1={0}
                y1={100 - threshold}
                x2={totalWidth}
                y2={100 - threshold}
                stroke="#c4b5fd"
                strokeWidth="0.4"
                strokeDasharray="2 3"
                vectorEffect="non-scaling-stroke"
            />
        </svg>
    );
}
