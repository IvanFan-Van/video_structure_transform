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
    const audioResult = useVideoStore((s) => s.audioResult);
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

                        {audioResult && (
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
                                        value: audioResult.bpm.toFixed(0),
                                        tip: "每分钟节拍数，反映音乐速度",
                                    },
                                    {
                                        label: "GENRE",
                                        value: audioResult.genre,
                                        tip: "AI 识别的音乐流派",
                                    },
                                    {
                                        label: "BRIGHT",
                                        value: `${(audioResult.spectral_centroid_mean / 1000).toFixed(1)}kHz`,
                                        tip: "全局频谱亮度质心频率，值越高音色越亮",
                                    },
                                    {
                                        label: "DURATION",
                                        value: `${audioResult.duration?.toFixed(1)}s`,
                                        tip: "音频总时长",
                                    },
                                    {
                                        label: "BEATS",
                                        value: `${audioResult.bpm.toFixed(0)} @ ${audioResult.beat_timings.length}`,
                                        tip: `节拍数 ${audioResult.beat_timings.length}，BPM ${audioResult.bpm.toFixed(0)}`,
                                    },
                                    {
                                        label: "RANGE",
                                        value: (audioResult.dynamic_range * 100).toFixed(1),
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

                        {audioResult && (
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
                                        data={audioResult.energy_curve}
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
                                    <Tooltip tip={"频谱质心 (Spectral Centroid) — 声音\u201C亮度\u201D的数学度量。数值越高代表高频能量越多、音色越亮（如镲片、尖锐嗓音）；越低则越低沉（如贝斯、底鼓）。曲线下降表示音色由亮转暗"} inline>BRIGHTNESS</Tooltip>
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
                                        data={audioResult.spectral_centroid}
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
                                    <Tooltip tip="频谱通量 (Spectral Flux) — 相邻两帧频谱的差异程度。数值越大说明这一时刻音频变化越剧烈（如新音符进入、打击乐敲击、语音转场），是检测音乐结构段落边界的常用指标" inline>FLUX</Tooltip>
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
                                        data={audioResult.spectral_flux}
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
                                    <Tooltip tip={"起始检测 (Onset Detection) — 标记音频中每个音符、节拍或声音事件的开始时刻。曲线中的峰值对应\u201C声音爆发点\u201D（如鼓点、人声起始），数值越高表示该时刻有新声音事件触发"} inline>ONSET</Tooltip>
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
                                        data={audioResult.onset_envelope}
                                        height={30}
                                    />
                                </div>
                            </div>
                        </div>
                        )}
                    </>
                )}
            </div>
        </BaseNode>
    );
}
