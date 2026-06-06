import { BaseNode } from "../ui/BaseNode";
import { CoverImage } from "../ui/CoverImage";
import { SplitSegment, SplitClipAsset } from "../../store/types";

interface Props {
    x: number;
    y: number;
    segment: SplitSegment;
    clip: SplitClipAsset | undefined;
    index: number;
    method: string;
    onPosChange: (id: string, x: number, y: number, w: number, h: number) => void;
}

export function SplitSegmentNode({
    x,
    y,
    segment,
    clip,
    index,
    method,
    onPosChange,
}: Props) {
    const meta = clip?.metadata;
    const nodeId = `split_segment_${index}`;

    return (
        <BaseNode
            x={x}
            y={y}
            w={220}
            title={`Segment ${index + 1}`}
            active={true}
            accent="#f97316"
            error={false}
            id={nodeId}
            onPosChange={onPosChange}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    fontSize: "10px",
                }}
            >
                <CoverImage
                    coverImageAssetId={clip?.cover_image_asset_id}
                    videoAssetId={clip?.asset_id}
                    alt={`Segment ${index + 1} cover`}
                    maxHeight={80}
                />
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "3px",
                    }}
                >
                    <SmallKV label="Start" value={`${segment.start_sec.toFixed(1)}s`} />
                    <SmallKV label="End" value={`${segment.end_sec.toFixed(1)}s`} />
                    <SmallKV label="Duration" value={`${segment.duration.toFixed(1)}s`} />
                    {segment.cut_score != null && (
                        <SmallKV
                            label="Score"
                            value={segment.cut_score.toFixed(1)}
                        />
                    )}
                    {segment.reason != null && (
                        <SmallKV label="Reason" value={segment.reason} />
                    )}
                </div>

                {meta && (
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns: "1fr 1fr",
                            gap: "3px",
                            paddingTop: "4px",
                            borderTop: "1px solid #f0f0f0",
                        }}
                    >
                        {meta.codec && (
                            <SmallKV label="Codec" value={meta.codec} />
                        )}
                        {meta.width && meta.height && (
                            <SmallKV
                                label="Res"
                                value={`${meta.width}x${meta.height}`}
                            />
                        )}
                        {meta.fps != null && (
                            <SmallKV
                                label="FPS"
                                value={meta.fps.toFixed(1)}
                            />
                        )}
                        {clip?.asset_id && (
                            <SmallKV
                                label="Asset"
                                value={clip.asset_id.slice(0, 8) + "..."}
                            />
                        )}
                    </div>
                )}
            </div>
        </BaseNode>
    );
}

function SmallKV({
    label,
    value,
}: {
    label: string;
    value: string;
}) {
    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                padding: "3px 4px",
                background: "#fafafa",
                borderRadius: "3px",
            }}
        >
            <span
                style={{
                    fontSize: "7px",
                    color: "#ccc",
                    letterSpacing: "0.5px",
                }}
            >
                {label}
            </span>
            <span
                style={{
                    fontSize: "9px",
                    color: "#666",
                    fontWeight: 500,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    maxWidth: "90px",
                }}
            >
                {value}
            </span>
        </div>
    );
}
