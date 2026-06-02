import { LossData } from "../../store/types";

export function LossChart({
    data,
    height = 70,
}: {
    data: LossData[];
    height?: number;
}) {
    if (!data.length) return null;
    const sm = [];
    let ema = data[0].loss;
    for (const d of data) {
        ema = 0.95 * ema + 0.05 * d.loss;
        sm.push(ema);
    }
    const mx = Math.max(...sm),
        mn = Math.min(...sm),
        rng = mx - mn || 1;
    const toY = (l: number) => ((mx - l) / rng) * 90 + 5;
    const toX = (i: number) => (i / Math.max(sm.length - 1, 1)) * 100;

    return (
        <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            style={{ width: "100%", height, display: "block" }}
        >
            {data.length < 400 &&
                data.map((d, i) => (
                    <circle
                        key={i}
                        cx={toX(i)}
                        cy={toY(Math.max(mn, Math.min(mx, d.loss)))}
                        r="0.3"
                        fill="#e8e8e8"
                        vectorEffect="non-scaling-stroke"
                    />
                ))}
            <polyline
                fill="none"
                stroke="#333"
                strokeWidth="1.2"
                points={sm.map((v, i) => `${toX(i)},${toY(v)}`).join(" ")}
                vectorEffect="non-scaling-stroke"
            />
            {sm.length > 1 && (
                <circle
                    cx={toX(sm.length - 1)}
                    cy={toY(sm[sm.length - 1])}
                    r="2"
                    fill="#333"
                    vectorEffect="non-scaling-stroke"
                />
            )}
            <text
                x="1"
                y="8"
                fontSize="5"
                fill="#ccc"
                vectorEffect="non-scaling-stroke"
            >
                {mx.toFixed(1)}
            </text>
            <text
                x="1"
                y="98"
                fontSize="5"
                fill="#ccc"
                vectorEffect="non-scaling-stroke"
            >
                {mn.toFixed(1)}
            </text>
        </svg>
    );
}
