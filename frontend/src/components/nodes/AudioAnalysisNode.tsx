import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
import { EnergyChart } from "../charts/EnergyChart";
import { CentroidChart } from "../charts/CentroidChart";
import { FluxChart } from "../charts/FluxChart";
import { OnsetChart } from "../charts/OnsetChart";

interface Props {
    x: number;
    y: number;
    onPosChange: (
        id: string,
        x: number,
        y: number,
        w: number,
        h: number,
    ) => void;
}

export function AudioAnalysisNode({ x, y, onPosChange }: Props) {
    const audioStatus = useVideoStore((s) => s.audioStatus);
    const audioGlobal = useVideoStore((s) => s.audioGlobal);
    const streamArr = useVideoStore((s) => s.streamArr);
    const videoErrors = useVideoStore((s) => s.videoErrors);
    const hasError = videoErrors.some((e) => e.nodeId === "audio");

    const hasData = audioStatus !== "idle";

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Audio Analysis"
            active={hasData}
            accent="#7c3aed"
            error={hasError}
            id="audio_analysis"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "6px" }}
            >
                {audioStatus === "idle" && (
                    <div
                        style={{
                            fontSize: "9px",
                            color: "#bbb",
                            textAlign: "center",
                            padding: "12px 0",
                        }}
                    >
                        Waiting for extraction...
                    </div>
                )}

                {hasData && (
                    <>
                        <div
                            style={{
                                fontSize: "10px",
                                fontWeight: 600,
                                color: "#7c3aed",
                                letterSpacing: "2px",
                                textAlign: "center",
                                marginBottom: "2px",
                            }}
                        >
                            {audioStatus === "done"
                                ? "✓ ANALYZED"
                                : "Analyzing..."}
                        </div>

                        {audioGlobal && (
                            <div
                                style={{
                                    display: "grid",
                                    gridTemplateColumns: "1fr 1fr",
                                    gap: "4px",
                                    fontSize: "10px",
                                    marginBottom: "2px",
                                }}
                            >
                                {[
                                    {
                                        label: "BPM",
                                        value: audioGlobal.estimated_bpm.toFixed(
                                            0,
                                        ),
                                    },
                                    { label: "GENRE", value: audioGlobal.genre },
                                    {
                                        label: "BRIGHT",
                                        value: `${(audioGlobal.overall_brightness_hz / 1000).toFixed(1)}kHz`,
                                    },
                                    {
                                        label: "DURATION",
                                        value: `${audioGlobal.duration?.toFixed(1)}s`,
                                    },
                                    {
                                        label: "RANGE",
                                        value: (
                                            audioGlobal.dynamic_range * 100
                                        ).toFixed(1),
                                    },
                                ].map(({ label, value }) => (
                                    <div
                                        key={label}
                                        style={{
                                            background: "#f8f8f8",
                                            borderRadius: "3px",
                                            padding: "5px 7px",
                                        }}
                                    >
                                        <div
                                            style={{
                                                fontSize: "7px",
                                                color: "#bbb",
                                                letterSpacing: "1px",
                                            }}
                                        >
                                            {label}
                                        </div>
                                        <div
                                            style={{
                                                fontWeight: 700,
                                                color: "#333",
                                                fontSize: "10px",
                                            }}
                                        >
                                            {value}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                gap: "4px",
                            }}
                        >
                            <div>
                                <div
                                    style={{
                                        fontSize: "7px",
                                        fontWeight: 600,
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                        marginBottom: "2px",
                                    }}
                                >
                                    ENERGY
                                </div>
                                <div
                                    style={{
                                        background: "#fafafa",
                                        borderRadius: "2px",
                                        border: "1px solid #f0f0f0",
                                        padding: "3px",
                                    }}
                                >
                                    <EnergyChart
                                        data={streamArr.map((c) => c.rms)}
                                        height={40}
                                    />
                                </div>
                            </div>

                            <div>
                                <div
                                    style={{
                                        fontSize: "7px",
                                        fontWeight: 600,
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                        marginBottom: "2px",
                                    }}
                                >
                                    BRIGHTNESS
                                </div>
                                <div
                                    style={{
                                        background: "#fafafa",
                                        borderRadius: "2px",
                                        border: "1px solid #f0f0f0",
                                        padding: "3px",
                                    }}
                                >
                                    <CentroidChart
                                        data={streamArr.map(
                                            (c) => c.spectral_centroid,
                                        )}
                                        height={40}
                                    />
                                </div>
                            </div>

                            <div>
                                <div
                                    style={{
                                        fontSize: "7px",
                                        fontWeight: 600,
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                        marginBottom: "2px",
                                    }}
                                >
                                    FLUX
                                </div>
                                <div
                                    style={{
                                        background: "#fafafa",
                                        borderRadius: "2px",
                                        border: "1px solid #f0f0f0",
                                        padding: "3px",
                                    }}
                                >
                                    <FluxChart
                                        data={streamArr.map(
                                            (c) => c.spectral_flux,
                                        )}
                                        height={30}
                                    />
                                </div>
                            </div>

                            <div>
                                <div
                                    style={{
                                        fontSize: "7px",
                                        fontWeight: 600,
                                        color: "#bbb",
                                        letterSpacing: "1px",
                                        marginBottom: "2px",
                                    }}
                                >
                                    ONSET
                                </div>
                                <div
                                    style={{
                                        background: "#fafafa",
                                        borderRadius: "2px",
                                        border: "1px solid #f0f0f0",
                                        padding: "3px",
                                    }}
                                >
                                    <OnsetChart
                                        data={streamArr.map(
                                            (c) => c.onset_envelope,
                                        )}
                                        height={30}
                                    />
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </BaseNode>
    );
}
