/** Downsample a number array to at most `maxPoints` using a sliding window. */
export function downsample(
    data: number[],
    maxPoints: number,
    strategy: "max" | "avg" = "avg",
): number[] {
    if (!data.length) return [];
    if (data.length <= maxPoints) return data;

    const win = Math.ceil(data.length / maxPoints);
    const result: number[] = [];
    for (let i = 0; i < data.length; i += win) {
        const chunk = data.slice(i, i + win);
        if (strategy === "max") {
            result.push(Math.max(...chunk));
        } else {
            result.push(chunk.reduce((a, b) => a + b, 0) / chunk.length);
        }
    }
    return result;
}

/** Split data into equal-sized windows and compute an aggregate for each window. */
export function aggregateWindows(
    data: number[],
    windowCount: number,
    strategy: "max" | "avg" = "avg",
): number[] {
    return downsample(data, windowCount, strategy);
}

/** Compute the mean of an array. */
export function mean(data: number[]): number {
    if (!data.length) return 0;
    return data.reduce((a, b) => a + b, 0) / data.length;
}
