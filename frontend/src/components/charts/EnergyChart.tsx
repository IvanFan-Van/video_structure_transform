import { useMemo } from "react";
import { downsample } from "../../utils/chart";

const MAX_POINTS = 100;

export function EnergyChart({
    data,
    height = 50,
}: {
    data: number[];
    height?: number;
}) {
    const points = useMemo(() => {
        if (!data.length) return null;
        const ds = downsample(data, MAX_POINTS, "avg");
        const mx = Math.max(...ds) || 1;
        const toY = (v: number) => 95 - (v / mx) * 80;
        const toX = (i: number) => (i / Math.max(ds.length - 1, 1)) * 100;
        return ds.map((v, i) => `${toX(i)},${toY(v)}`).join(" ");
    }, [data]);

    if (!points) return null;

    const areaPoints = `0,95 ${points} 100,95`;

    return (
        <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            style={{ width: "100%", height, display: "block" }}
        >
            <defs>
                <linearGradient id="energyGrad" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.25" />
                    <stop
                        offset="100%"
                        stopColor="#7c3aed"
                        stopOpacity="0.02"
                    />
                </linearGradient>
            </defs>
            <polygon points={areaPoints} fill="url(#energyGrad)" />
            <polyline
                fill="none"
                stroke="#7c3aed"
                strokeWidth="1.2"
                points={points}
                vectorEffect="non-scaling-stroke"
            />
        </svg>
    );
}
