import { useState, useMemo } from "react";
import { BaseNode } from "../ui/BaseNode";
import { ActionButton } from "../ui/ActionButton";
import { StatusHeader } from "../ui/StatusHeader";
import { useVideoStore } from "../../store/useVideoStore";
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

const NODE_ID = "plan_generate";

export function GenerateNode({ x, y, onPosChange }: Props) {
    const { hasError } = useNodeError(NODE_ID);

    const planResult = useVideoStore((s) => s.planResult);
    const generateStatus = useVideoStore((s) => s.generateStatus);
    const generateTime = useVideoStore((s) => s.generateTime);
    const generateResult = useVideoStore((s) => s.generateResult);
    const startSlotGenerate = useVideoStore((s) => s.startSlotGenerate);
    const stopSlotGenerate = useVideoStore((s) => s.stopSlotGenerate);

    const pendingSummary = useMemo(() => {
        if (!planResult?.segments) return null;
        const byType: Record<string, { count: number; segments: number[] }> =
            {};
        for (const seg of planResult.segments) {
            for (const slot of seg.slots) {
                if (slot.status === "pending") {
                    if (!byType[slot.slot_type]) {
                        byType[slot.slot_type] = { count: 0, segments: [] };
                    }
                    byType[slot.slot_type].count++;
                    if (!byType[slot.slot_type].segments.includes(seg.index)) {
                        byType[slot.slot_type].segments.push(seg.index);
                    }
                }
            }
        }
        const entries = Object.entries(byType);
        const total = entries.reduce((s, [, v]) => s + v.count, 0);
        return { entries, total };
    }, [planResult]);

    const hasPending = (pendingSummary?.total ?? 0) > 0;

    return (
        <BaseNode
            x={x}
            y={y}
            w={260}
            title="Generate All"
            active={hasPending || generateStatus !== "idle"}
            accent="#6366f1"
            error={hasError}
            id={NODE_ID}
            onPosChange={onPosChange}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    fontSize: "10px",
                }}
            >
                {/* ── Idle state ── */}
                {(generateStatus === "idle" ||
                    generateStatus === "cancelled" ||
                    generateStatus === "error") && (
                    <>
                        {pendingSummary && pendingSummary.total > 0 ? (
                            <>
                                <div
                                    style={{
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: "3px",
                                    }}
                                >
                                    <div
                                        style={{
                                            fontSize: "7px",
                                            fontWeight: 600,
                                            letterSpacing: "1px",
                                            color: "#bbb",
                                        }}
                                    >
                                        PENDING SLOTS
                                    </div>
                                    {pendingSummary.entries.map(
                                        ([type, info]) => (
                                            <div
                                                key={type}
                                                style={{
                                                    display: "flex",
                                                    justifyContent:
                                                        "space-between",
                                                    fontSize: "7px",
                                                    color: "#555",
                                                }}
                                            >
                                                <span>
                                                    {type} ×{info.count}
                                                </span>
                                                <span
                                                    style={{
                                                        color: "#bbb",
                                                        fontSize: "6.5px",
                                                    }}
                                                >
                                                    seg{" "}
                                                    {info.segments
                                                        .map((i) => i + 1)
                                                        .join(", ")}
                                                </span>
                                            </div>
                                        ),
                                    )}
                                    <div
                                        style={{
                                            borderTop: "1px solid #f0f0f0",
                                            paddingTop: "3px",
                                            fontSize: "7px",
                                            fontWeight: 600,
                                            color: "#333",
                                        }}
                                    >
                                        Total: {pendingSummary.total} slots
                                    </div>
                                </div>
                                <ActionButton
                                    variant="primary"
                                    label={`▶ Generate ${pendingSummary.total} Slots`}
                                    enabled={true}
                                    accent="#6366f1"
                                    onClick={startSlotGenerate}
                                    style={{ fontSize: "8px" }}
                                />
                            </>
                        ) : (
                            <>
                                <div
                                    style={{
                                        fontSize: "7px",
                                        color: "#bbb",
                                        textAlign: "center",
                                        padding: "6px 0",
                                    }}
                                >
                                    No pending slots.
                                    <br />
                                    Mark slots as &quot;AI Gen&quot; in Slot
                                    nodes first.
                                </div>
                                <ActionButton
                                    variant="muted"
                                    label="▶ Generate All"
                                    enabled={false}
                                    accent="#6366f1"
                                    onClick={() => {}}
                                    style={{ fontSize: "8px" }}
                                />
                            </>
                        )}

                        {generateStatus === "error" && (
                            <StatusHeader
                                variant="error"
                                label="Generation failed"
                            />
                        )}
                    </>
                )}

                {/* ── Loading state ── */}
                {generateStatus === "loading" && (
                    <>
                        <StatusHeader
                            variant="loading"
                            label="Generating..."
                            accent="#6366f1"
                        />
                        <ActionButton
                            variant="muted"
                            label="■ Stop"
                            onClick={stopSlotGenerate}
                            style={{ fontSize: "7px" }}
                        />
                        {generateTime != null && (
                            <div
                                style={{
                                    fontSize: "7px",
                                    color: "#aaa",
                                    textAlign: "center",
                                }}
                            >
                                {generateTime.toFixed(1)}s
                            </div>
                        )}
                    </>
                )}

                {/* ── Success state ── */}
                {generateStatus === "success" && generateResult && (
                    <>
                        <StatusHeader
                            variant="success"
                            label="Generated"
                            accent="#6366f1"
                        />
                        <div
                            style={{
                                textAlign: "center",
                                fontSize: "8px",
                                color: "#555",
                            }}
                        >
                            {generateResult.generated_slots.length} slot
                            {generateResult.generated_slots.length !== 1
                                ? "s"
                                : ""}{" "}
                            filled
                        </div>
                        <ActionButton
                            variant="muted"
                            label="↻ Re-generate"
                            onClick={startSlotGenerate}
                            style={{ fontSize: "7px" }}
                        />
                    </>
                )}
            </div>
        </BaseNode>
    );
}
