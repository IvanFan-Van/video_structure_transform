import { useState, useRef } from "react";
import { BaseNode } from "../ui/BaseNode";
import { ActionButton } from "../ui/ActionButton";
import { StatusHeader } from "../ui/StatusHeader";
import { AccordionItem } from "../ui/AccordionItem";
import { useVideoStore } from "../../store/useVideoStore";
import { useNodeError } from "../../hooks/useNodeError";

interface Props {
    x: number;
    y: number;
    segmentIndex: number;
    onPosChange: (id: string, x: number, y: number, w: number, h: number) => void;
}

const TEXT_SLOT_TYPES = new Set(["visual_text", "narration"]);

function formatTime(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}

export function SlotNode({ x, y, segmentIndex, onPosChange }: Props) {
    const nodeId = `slot_segment_${segmentIndex}`;
    const { hasError } = useNodeError(nodeId);

    const planResult = useVideoStore((s) => s.planResult);
    const slotFillStatuses = useVideoStore((s) => s.slotFillStatuses);
    const fillSlot = useVideoStore((s) => s.fillSlot);
    const quickUpload = useVideoStore((s) => s.quickUpload);

    const segment = planResult?.segments[segmentIndex];
    const planId = planResult?.plan_id;

    const [slotTexts, setSlotTexts] = useState<Record<string, string>>({});
    const [expandedSlots, setExpandedSlots] = useState(true);
    const [uploadingSlot, setUploadingSlot] = useState<string | null>(null);
    const fileRef = useRef<HTMLInputElement>(null);
    const [targetSlot, setTargetSlot] = useState<string | null>(null);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !targetSlot || !planId) return;
        setUploadingSlot(targetSlot);
        const assetId = await quickUpload(file);
        if (assetId) {
            await fillSlot(planId, targetSlot, "user_upload", assetId);
        }
        setUploadingSlot(null);
        setTargetSlot(null);
    };

    const triggerUpload = (slotId: string) => {
        setTargetSlot(slotId);
        fileRef.current?.click();
    };

    if (!segment) return null;

    const stageLabel = segment.stage.charAt(0).toUpperCase() + segment.stage.slice(1);

    return (
        <BaseNode
            x={x}
            y={y}
            w={320}
            title={`Slots – ${stageLabel}`}
            active={true}
            accent="#ec4899"
            error={hasError}
            id={nodeId}
            onPosChange={onPosChange}
        >
            <input
                ref={fileRef}
                type="file"
                accept="video/*,image/*,audio/*"
                style={{ display: "none" }}
                onChange={handleFileSelect}
            />

            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    fontSize: "10px",
                }}
            >
                {/* ── Segment header ── */}
                <div
                    style={{
                        fontSize: "9px",
                        color: "#555",
                        lineHeight: "1.4",
                        wordBreak: "break-word",
                    }}
                >
                    {segment.narrative_intent}
                </div>
                <div
                    style={{
                        fontSize: "8px",
                        color: "#bbb",
                    }}
                >
                    {formatTime(segment.start_time)} —{" "}
                    {formatTime(segment.end_time)}
                </div>

                <AccordionItem
                    open={expandedSlots}
                    onToggle={() => setExpandedSlots((o) => !o)}
                    title={`Slots (${segment.slots.length})`}
                    accent="#ec4899"
                    accentBg="#fdf2f8"
                    accentBorder="#fbcfe8"
                >
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "6px",
                        }}
                    >
                        {segment.slots.map((slot) => {
                            const isText = TEXT_SLOT_TYPES.has(slot.slot_type);
                            const text =
                                slotTexts[slot.slot_id] ??
                                (slot.status === "filled" &&
                                slot.fill_method === "manual_input"
                                    ? slot.value ?? ""
                                    : "");
                            const fillStatus: string =
                                slotFillStatuses[slot.slot_id] ??
                                (slot.status === "filled" ||
                                slot.status === "pending"
                                    ? slot.status
                                    : "empty");
                            const statusColor =
                                fillStatus === "filled"
                                    ? "#22c55e"
                                    : fillStatus === "pending"
                                      ? "#f59e0b"
                                      : fillStatus === "filling"
                                        ? "#3b82f6"
                                        : fillStatus === "error"
                                          ? "#ef4444"
                                          : "#d1d5db";

                            const statusLabel =
                                fillStatus === "filled"
                                    ? "Filled"
                                    : fillStatus === "pending"
                                      ? "Pending"
                                      : fillStatus === "filling"
                                        ? "Uploading…"
                                        : fillStatus === "error"
                                          ? "Error"
                                          : "Empty";

                            return (
                                <div
                                    key={slot.slot_id}
                                    style={{
                                        padding: "6px 8px",
                                        background: "#f9fafb",
                                        borderRadius: "4px",
                                        border: "1px solid #f0f0f0",
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: "4px",
                                    }}
                                >
                                    {/* Slot header */}
                                    <div
                                        style={{
                                            display: "flex",
                                            justifyContent: "space-between",
                                            alignItems: "center",
                                        }}
                                    >
                                        <span
                                            style={{
                                                fontSize: "8px",
                                                fontWeight: 600,
                                                color: "#666",
                                                padding: "1px 6px",
                                                background: "#f0f0f0",
                                                borderRadius: "3px",
                                            }}
                                        >
                                            {slot.slot_type}
                                        </span>
                                        <span
                                            style={{
                                                fontSize: "7px",
                                                fontWeight: 600,
                                                color: statusColor,
                                            }}
                                        >
                                            ● {statusLabel}
                                        </span>
                                    </div>

                                    {/* Description */}
                                    <div
                                        style={{
                                            fontSize: "8px",
                                            color: "#888",
                                            lineHeight: "1.4",
                                        }}
                                    >
                                        {slot.description}
                                    </div>

                                    {/* Constraints */}
                                    {slot.constraints &&
                                        Object.keys(slot.constraints).length >
                                            0 && (
                                            <div
                                                style={{
                                                    fontSize: "7px",
                                                    color: "#aaa",
                                                    display: "flex",
                                                    flexWrap: "wrap",
                                                    gap: "2px 6px",
                                                }}
                                            >
                                                {Object.entries(
                                                    slot.constraints,
                                                ).map(([k, v]) => (
                                                    <span key={k}>
                                                        {k}:{" "}
                                                        {String(v)}
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                    {/* Filled value display */}
                                    {slot.status === "filled" &&
                                        slot.value && (
                                            <div
                                                style={{
                                                    fontSize: "7px",
                                                    color: "#22c55e",
                                                    overflow: "hidden",
                                                    textOverflow: "ellipsis",
                                                    whiteSpace: "nowrap",
                                                }}
                                                title={slot.value}
                                            >
                                                ✓ {slot.value.slice(0, 20)}
                                                {slot.value.length > 20
                                                    ? "…"
                                                    : ""}
                                            </div>
                                        )}

                                    {/* Text input for text-type slots */}
                                    {isText &&
                                        (fillStatus === "empty" ||
                                            fillStatus === "error") && (
                                            <>
                                                <textarea
                                                    value={text}
                                                    onChange={(e) =>
                                                        setSlotTexts((p) => ({
                                                            ...p,
                                                            [slot.slot_id]:
                                                                e.target
                                                                    .value,
                                                        }))
                                                    }
                                                    placeholder="Enter text..."
                                                    rows={2}
                                                    style={{
                                                        width: "100%",
                                                        padding: "4px 6px",
                                                        fontSize: "8px",
                                                        fontFamily: "inherit",
                                                        border: "1px solid #e0e0e0",
                                                        borderRadius: "3px",
                                                        resize: "vertical",
                                                        background: "#fff",
                                                        color: "#333",
                                                        outline: "none",
                                                        boxSizing: "border-box",
                                                    }}
                                                    onFocus={(e) =>
                                                        (e.currentTarget.style.borderColor =
                                                            "#ec4899")
                                                    }
                                                    onBlur={(e) =>
                                                        (e.currentTarget.style.borderColor =
                                                            "#e0e0e0")
                                                    }
                                                />
                                                <div
                                                    style={{
                                                        display: "flex",
                                                        gap: "4px",
                                                    }}
                                                >
                                                    <ActionButton
                                                        variant="primary"
                                                        label="Save"
                                                        enabled={
                                                            text.trim()
                                                                .length > 0
                                                        }
                                                        accent="#ec4899"
                                                        onClick={() =>
                                                            fillSlot(
                                                                planId!,
                                                                slot.slot_id,
                                                                "manual_input",
                                                                text.trim(),
                                                            )
                                                        }
                                                        style={{
                                                            fontSize: "8px",
                                                            padding:
                                                                "3px 8px",
                                                        }}
                                                    />
                                                    <ActionButton
                                                        variant="muted"
                                                        label="AI Gen"
                                                        onClick={() =>
                                                            fillSlot(
                                                                planId!,
                                                                slot.slot_id,
                                                                "ai_generate",
                                                            )
                                                        }
                                                        style={{
                                                            fontSize: "8px",
                                                            padding: "3px 8px",
                                                        }}
                                                    />
                                                </div>
                                            </>
                                        )}

                                    {/* Asset input for non-text slots */}
                                    {!isText &&
                                        (fillStatus === "empty" ||
                                            fillStatus === "error") && (
                                            <div
                                                style={{
                                                    display: "flex",
                                                    gap: "4px",
                                                }}
                                            >
                                                <ActionButton
                                                    variant="primary"
                                                    label={
                                                        uploadingSlot ===
                                                        slot.slot_id
                                                            ? "Uploading…"
                                                            : "Upload"
                                                    }
                                                    enabled={
                                                        uploadingSlot !==
                                                        slot.slot_id
                                                    }
                                                    accent="#ec4899"
                                                    onClick={() =>
                                                        triggerUpload(
                                                            slot.slot_id,
                                                        )
                                                    }
                                                    style={{
                                                        fontSize: "8px",
                                                        padding: "3px 8px",
                                                    }}
                                                />
                                                <ActionButton
                                                    variant="muted"
                                                    label="AI Gen"
                                                    onClick={() =>
                                                        fillSlot(
                                                            planId!,
                                                            slot.slot_id,
                                                            "ai_generate",
                                                        )
                                                    }
                                                    style={{
                                                        fontSize: "8px",
                                                        padding: "3px 8px",
                                                    }}
                                                />
                                            </div>
                                        )}

                                    {/* Filled non-text: show re-fill option */}
                                    {!isText &&
                                        (fillStatus === "filled" ||
                                            fillStatus === "pending") && (
                                            <ActionButton
                                                variant="muted"
                                                label="↻ Refill"
                                                onClick={() =>
                                                    triggerUpload(
                                                        slot.slot_id,
                                                    )
                                                }
                                                style={{
                                                    fontSize: "8px",
                                                    padding: "3px 8px",
                                                }}
                                            />
                                        )}
                                </div>
                            );
                        })}
                    </div>
                </AccordionItem>
            </div>
        </BaseNode>
    );
}
