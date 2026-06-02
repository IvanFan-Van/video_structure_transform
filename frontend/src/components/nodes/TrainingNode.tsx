import { useAppStore } from "../../store/useAppStore";
import { BaseNode } from "../ui/BaseNode";
import { LossChart } from "../charts/LossChart";
import { fmt } from "../../utils";

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

export function TrainingNode({ x, y, onPosChange }: Props) {
    const dataset = useAppStore((s) => s.dataset);
    const config = useAppStore((s) => s.config);
    const training = useAppStore((s) => s.training);
    const modelReady = useAppStore((s) => s.modelReady);
    const currentStep = useAppStore((s) => s.currentStep);
    const currentLoss = useAppStore((s) => s.currentLoss);
    const currentSample = useAppStore((s) => s.currentSample);
    const stepTime = useAppStore((s) => s.stepTime);
    const totalTime = useAppStore((s) => s.totalTime);
    const lossHistory = useAppStore((s) => s.lossHistory);
    const startTraining = useAppStore((s) => s.startTraining);
    const stopTraining = useAppStore((s) => s.stopTraining);

    return (
        <BaseNode
            x={x}
            y={y}
            w={300}
            title="Training"
            active={training || modelReady}
            accent="#22c55e"
            id="training"
            onPosChange={onPosChange}
        >
            <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
                {!training && !modelReady && (
                    <button
                        onClick={startTraining}
                        disabled={!dataset}
                        style={{
                            padding: "10px",
                            fontSize: "11px",
                            fontWeight: 600,
                            fontFamily: "inherit",
                            letterSpacing: "1px",
                            background: dataset ? "#333" : "#e8e8e8",
                            color: dataset ? "#fff" : "#bbb",
                            border: "none",
                            borderRadius: "3px",
                            cursor: dataset ? "pointer" : "not-allowed",
                        }}
                    >
                        ▶ TRAIN
                    </button>
                )}
                {training && (
                    <>
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                fontSize: "10px",
                                color: "#999",
                            }}
                        >
                            <span>
                                step {currentStep}/{config.num_steps}
                            </span>
                            <span>loss {currentLoss.toFixed(4)}</span>
                        </div>
                        <div
                            style={{
                                height: "2px",
                                background: "#f0f0f0",
                                borderRadius: "1px",
                                overflow: "hidden",
                            }}
                        >
                            <div
                                style={{
                                    height: "100%",
                                    width:
                                        (currentStep / config.num_steps) * 100 +
                                        "%",
                                    background: "#333",
                                    transition: "width 0.1s",
                                }}
                            />
                        </div>
                        <LossChart data={lossHistory} height={50} />
                        {currentSample && (
                            <div style={{ fontSize: "10px", color: "#888" }}>
                                sample:{" "}
                                <span
                                    style={{ color: "#333", fontWeight: 600 }}
                                >
                                    {currentSample}
                                </span>
                            </div>
                        )}
                        <div style={{ fontSize: "9px", color: "#bbb" }}>
                            {stepTime}ms/step · {fmt(totalTime)} elapsed
                        </div>
                        <button
                            onClick={stopTraining}
                            style={{
                                padding: "5px",
                                fontSize: "9px",
                                fontFamily: "inherit",
                                background: "transparent",
                                border: "1px solid #e0e0e0",
                                borderRadius: "3px",
                                color: "#999",
                                cursor: "pointer",
                            }}
                        >
                            ■ STOP
                        </button>
                    </>
                )}
                {modelReady && (
                    <div style={{ textAlign: "center" }}>
                        <div
                            style={{
                                fontSize: "10px",
                                fontWeight: 600,
                                color: "#22c55e",
                                letterSpacing: "2px",
                                marginBottom: "4px",
                            }}
                        >
                            ✓ GPT READY
                        </div>
                        <div
                            style={{
                                fontSize: "9px",
                                color: "#bbb",
                                marginBottom: "8px",
                            }}
                        >
                            loss {currentLoss.toFixed(4)} · {config.num_steps}{" "}
                            steps · {fmt(totalTime)}
                        </div>
                        <div
                            style={{
                                display: "flex",
                                gap: "6px",
                                justifyContent: "center",
                            }}
                        >
                            <button
                                onClick={startTraining}
                                style={{
                                    padding: "5px 10px",
                                    fontSize: "9px",
                                    fontFamily: "inherit",
                                    background: "transparent",
                                    border: "1px solid #e0e0e0",
                                    borderRadius: "3px",
                                    color: "#999",
                                    cursor: "pointer",
                                }}
                            >
                                RETRAIN
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </BaseNode>
    );
}
