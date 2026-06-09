import { useState, useRef, useEffect } from "react";
import { BaseNode } from "../ui/BaseNode";
import { ActionButton } from "../ui/ActionButton";
import { AccordionItem } from "../ui/AccordionItem";
import { Tooltip } from "../ui/Tooltip";
import { useVideoStore } from "../../store/useVideoStore";
import { useNodeError } from "../../hooks/useNodeError";

interface Props {
    x: number;
    y: number;
    segmentIndex: number;
    onPosChange: (
        id: string,
        x: number,
        y: number,
        w: number,
        h: number,
    ) => void;
}

const TEXT_SLOT_TYPES = new Set(["visual_text", "narration"]);

const SLOT_TIPS: Record<string, string> = {
    visual_text: "画面文字/字幕内容，会直接显示在视频画面上",
    narration: "旁白/配音文本，由 TTS 引擎转换为语音",
    visual_asset: "画面素材（视频片段/图片），直接放入时间线对应位置",
    audio_asset: "音频素材（BGM/音效），叠加到对应时间段",
};

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

    type SlotMode = "manual_input" | "ai_generate" | "user_upload";
    const [slotModes, setSlotModes] = useState<Record<string, SlotMode>>({});

    useEffect(() => {
        if (!segment) return;
        const init: Record<string, SlotMode> = {};
        for (const slot of segment.slots) {
            if (slot.status === "filled" || slot.status === "pending") {
                init[slot.slot_id] =
                    (slot.fill_method as SlotMode) ?? "ai_generate";
            }
        }
        setSlotModes((prev) => ({ ...init, ...prev }));
    }, [segment?.slots]);

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

    const stageLabel =
        segment.stage.charAt(0).toUpperCase() + segment.stage.slice(1);

    return (
        <BaseNode
            x={x}
            y={y}
            w={290}
            title={`Slots – ${stageLabel}`}
            active={true}
            accent="#ec4899"
            error={hasError}
            id={nodeId}
            tourId={nodeId}
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
                    gap: "5px",
                    fontSize: "10px",
                }}
            >
                <div
                    style={{
                        fontSize: "8px",
                        color: "#555",
                        lineHeight: "1.4",
                        wordBreak: "break-word",
                    }}
                >
                    {segment.narrative_intent}
                </div>
                <div style={{ fontSize: "7px", color: "#bbb" }}>
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
                            gap: "5px",
                        }}
                    >
                        {segment.slots.map((slot) => {
                            const isText = TEXT_SLOT_TYPES.has(slot.slot_type);
                            const currentMode: SlotMode =
                                slotModes[slot.slot_id] ??
                                (isText ? "manual_input" : "user_upload");
                            const text =
                                slotTexts[slot.slot_id] ??
                                (slot.status === "filled" && slot.value
                                    ? slot.value
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

                            const actions: { mode: SlotMode; label: string }[] =
                                isText
                                    ? [
                                          {
                                              mode: "manual_input",
                                              label: "Manual",
                                          },
                                          {
                                              mode: "ai_generate",
                                              label: "AI",
                                          },
                                      ]
                                    : [
                                          {
                                              mode: "user_upload",
                                              label: "Upload",
                                          },
                                          {
                                              mode: "ai_generate",
                                              label: "AI",
                                          },
                                      ];

                            const actionLabel =
                                currentMode === "manual_input"
                                    ? "Save"
                                    : currentMode === "user_upload"
                                      ? uploadingSlot === slot.slot_id
                                          ? "…"
                                          : "Upload"
                                      : "Mark";

                            const handleAction = () => {
                                if (currentMode === "manual_input") {
                                    if (text.trim().length > 0) {
                                        fillSlot(
                                            planId!,
                                            slot.slot_id,
                                            "manual_input",
                                            text.trim(),
                                        );
                                    }
                                } else if (currentMode === "user_upload") {
                                    triggerUpload(slot.slot_id);
                                } else {
                                    fillSlot(
                                        planId!,
                                        slot.slot_id,
                                        "ai_generate",
                                    );
                                }
                            };

                            return (
                                <div
                                    key={slot.slot_id}
                                    style={{
                                        padding: "5px 7px",
                                        background: "#f9fafb",
                                        borderRadius: "3px",
                                        border: "1px solid #f0f0f0",
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: "3px",
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
                                        {(() => {
                                            let slotTip =
                                                SLOT_TIPS[slot.slot_type];
                                            if (!slotTip) {
                                                const s = slot.slot_type || "";
                                                slotTip =
                                                    s.includes("visual") ||
                                                    s.includes("image")
                                                        ? "视觉素材槽位"
                                                        : s.includes("audio") ||
                                                            s.includes("bgm")
                                                          ? "音频素材槽位"
                                                          : "";
                                            }
                                            return (
                                                <Tooltip
                                                    tip={slotTip || ""}
                                                    inline
                                                >
                                                    <span
                                                        style={{
                                                            fontSize: "8px",
                                                            fontWeight: 600,
                                                            color: "#666",
                                                            padding: "1px 6px",
                                                            background:
                                                                "#f0f0f0",
                                                            borderRadius: "3px",
                                                        }}
                                                    >
                                                        {slot.slot_type}
                                                    </span>
                                                </Tooltip>
                                            );
                                        })()}
                                        <span
                                            style={{
                                                fontSize: "6.5px",
                                                fontWeight: 600,
                                                color: statusColor,
                                            }}
                                        >
                                            ● {statusLabel}
                                            {fillStatus === "pending" &&
                                                " \u2014 AI queue"}
                                        </span>
                                    </div>

                                    {/* Description */}
                                    <div
                                        style={{
                                            fontSize: "7px",
                                            color: "#888",
                                            lineHeight: "1.4",
                                        }}
                                    >
                                        {slot.description}
                                    </div>

                                    {/* Constraints */}
                                    {(() => {
                                        const filtered = Object.entries(
                                            slot.constraints ?? {},
                                        ).filter(([, v]) => v != null);
                                        if (filtered.length === 0) return null;
                                        return (
                                            <div
                                                style={{
                                                    fontSize: "6.5px",
                                                    color: "#aaa",
                                                    display: "flex",
                                                    flexWrap: "wrap",
                                                    gap: "2px 6px",
                                                }}
                                            >
                                                {filtered.map(([k, v]) => (
                                                    <span key={k}>
                                                        {k}: {String(v)}
                                                    </span>
                                                ))}
                                            </div>
                                        );
                                    })()}

                                    {/* Current value preview */}
                                    {slot.status === "filled" && slot.value && (
                                        <div
                                            style={{
                                                fontSize: "6.5px",
                                                color: "#22c55e",
                                                overflow: "hidden",
                                                textOverflow: "ellipsis",
                                                whiteSpace: "nowrap",
                                            }}
                                            title={slot.value}
                                        >
                                            ✓ {slot.value.slice(0, 24)}
                                            {slot.value.length > 24 ? "…" : ""}
                                        </div>
                                    )}

                                    {/* Text input (always visible for text slots) */}
                                    {isText && (
                                        <textarea
                                            value={text}
                                            onChange={(e) =>
                                                setSlotTexts((p) => ({
                                                    ...p,
                                                    [slot.slot_id]:
                                                        e.target.value,
                                                }))
                                            }
                                            placeholder="Enter text..."
                                            rows={2}
                                            style={{
                                                width: "100%",
                                                padding: "3px 5px",
                                                fontSize: "7px",
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
                                    )}

                                    {/* Mode switch + action button same row */}
                                    <div
                                        style={{
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "4px",
                                        }}
                                    >
                                        {/* Mode pill switch */}
                                        <div
                                            style={{
                                                display: "flex",
                                                flex: 1,
                                                border: "1px solid #e0e0e0",
                                                borderRadius: "4px",
                                                overflow: "hidden",
                                            }}
                                        >
                                            {actions.map((a, ai) => (
                                                <button
                                                    key={a.mode}
                                                    onClick={() =>
                                                        setSlotModes((p) => ({
                                                            ...p,
                                                            [slot.slot_id]:
                                                                a.mode,
                                                        }))
                                                    }
                                                    style={{
                                                        flex: 1,
                                                        padding: "2px 4px",
                                                        fontSize: "7px",
                                                        fontFamily: "inherit",
                                                        fontWeight: 600,
                                                        cursor: "pointer",
                                                        color:
                                                            currentMode ===
                                                            a.mode
                                                                ? "#fff"
                                                                : "#aaa",
                                                        background:
                                                            currentMode ===
                                                            a.mode
                                                                ? "#ec4899"
                                                                : "transparent",
                                                        border: "none",
                                                        borderLeft:
                                                            ai > 0
                                                                ? "1px solid #e0e0e0"
                                                                : "none",
                                                        outline: "none",
                                                    }}
                                                >
                                                    {a.label}
                                                </button>
                                            ))}
                                        </div>

                                        {/* Action button */}
                                        <ActionButton
                                            variant="primary"
                                            label={actionLabel}
                                            enabled={
                                                currentMode === "manual_input"
                                                    ? text.trim().length > 0
                                                    : currentMode ===
                                                        "user_upload"
                                                      ? uploadingSlot !==
                                                        slot.slot_id
                                                      : true
                                            }
                                            accent="#ec4899"
                                            onClick={handleAction}
                                            style={{
                                                fontSize: "7px",
                                                padding: "2px 8px",
                                            }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </AccordionItem>
            </div>
        </BaseNode>
    );
}
