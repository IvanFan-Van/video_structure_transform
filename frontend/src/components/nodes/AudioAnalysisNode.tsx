import { useVideoStore } from "../../store/useVideoStore";
import { BaseNode } from "../ui/BaseNode";
import { Tooltip } from "../ui/Tooltip";
import { EnergyChart } from "../charts/EnergyChart";
import { CentroidChart } from "../charts/CentroidChart";
import { FluxChart } from "../charts/FluxChart";
import { OnsetChart } from "../charts/OnsetChart";
import { StatusHeader } from "../ui/StatusHeader";
import { useNodeError } from "../../hooks/useNodeError";

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
    const { hasError } = useNodeError("audio");

    const hasData = audioStatus !== "idle" && audioStatus !== "cancelled";

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Audio Analysis"
            active={hasData}
            accent="#f59e0b"
            error={hasError}
            id="audio_analysis"
            tourId="audio_analysis"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "6px" }}
            >
                {(audioStatus === "idle" || audioStatus === "cancelled") && (
                    <StatusHeader
                        variant="idle"
                        label="Waiting for extraction..."
                    />
                )}

                {hasData && (
                    <>
                        {audioStatus === "loading" ? (
                            <StatusHeader
                                variant="loading"
                                label="Analyzing"
                                accent="#f59e0b"
                            />
                        ) : (
                            <StatusHeader
                                variant="success"
                                label="ANALYZED"
                                accent="#f59e0b"
                            />
                        )}

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
                                        tip: "每分钟节拍数，反映音乐速度",
                                    },
                                    {
                                        label: "GENRE",
                                        value: audioGlobal.genre,
                                        tip: "AI 识别的音乐流派",
                                    },
                                    {
                                        label: "BRIGHT",
                                        value: `${(audioGlobal.overall_brightness_hz / 1000).toFixed(1)}kHz`,
                                        tip: "频谱亮度质心频率，值越高音色越亮",
                                    },
                                    {
                                        label: "DURATION",
                                        value: `${audioGlobal.duration?.toFixed(1)}s`,
                                        tip: "音频总时长",
                                    },
                                    {
                                        label: "RANGE",
                                        value: (
                                            audioGlobal.dynamic_range * 100
                                        ).toFixed(1),
                                        tip: "动态范围，音量变化的幅度",
                                    },
                                ].map(({ label, value, tip }) => (
                                    <div
                                        key={label}
                                        style={{
                                            background: "#f8f8f8",
                                            borderRadius: "3px",
                                            padding: "5px 7px",
                                        }}
                                    >
                                        <Tooltip tip={tip} inline>
                                        <div
                                            style={{
                                                fontSize: "7px",
                                                color: "#bbb",
                                                letterSpacing: "1px",
                                                display: "inline-block",
                                            }}
                                        >
                                            {label}
                                        </div>
                                        </Tooltip>
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
                                        display: "inline-block",
                                    }}
                                >
                                    <Tooltip tip="RMS 能量随时间变化曲线，反映音量起伏" inline>ENERGY</Tooltip>
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
                                        display: "inline-block",
                                    }}
                                >
                                    <Tooltip tip="频谱质心随时间变化，反映音色明亮度分布" inline>BRIGHTNESS</Tooltip>
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
                                        display: "inline-block",
                                    }}
                                >
                                    <Tooltip tip="频谱通量，相邻帧频谱差异，反映音频变化剧烈程度" inline>FLUX</Tooltip>
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
                                        display: "inline-block",
                                    }}
                                >
                                    <Tooltip tip="音符起始检测，标记每个音符/节拍的开始时刻" inline>ONSET</Tooltip>
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
