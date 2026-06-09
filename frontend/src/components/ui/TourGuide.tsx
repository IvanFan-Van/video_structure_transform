import { useEffect, useRef } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";
import type { DriveStep } from "driver.js";

interface Props {
    onClose: () => void;
    planResultReady: boolean;
}

function sel(id: string) {
    return `[data-tour="${id}"]`;
}

export function TourGuide({ onClose, planResultReady }: Props) {
    const started = useRef(false);

    useEffect(() => {
        if (started.current) return;
        started.current = true;

        const steps: DriveStep[] = [
            {
                element: sel("reference"),
                popover: {
                    title: "1. Upload Reference Video",
                    description:
                        "Drag and drop or click to upload a viral video you want to analyze. Supported formats: .mp4 .mov .avi .mkv .webm",
                    side: "bottom",
                },
            },
            {
                element: sel("compress_config"),
                popover: {
                    title: "2. Configure Compression",
                    description:
                        "Set video codec, quality (CRF), resolution, frame rate, and audio codec. These determine the output video specs used in later steps.",
                    side: "bottom",
                },
            },
            {
                element: sel("compress"),
                popover: {
                    title: "3. Compress Video",
                    description:
                        "Click COMPRESS to transcode the video. A before/after comparison will show the size savings.",
                    side: "bottom",
                },
            },
            {
                element: sel("extracting"),
                popover: {
                    title: "4. Extract Analysis Data",
                    description:
                        "Run three parallel analyses: Script Structure (transcript + narrative stages), BGM Features (tempo/genre), and Video Features (shots/camera/transitions).",
                    side: "bottom",
                },
            },
            {
                element: sel("split"),
                popover: {
                    title: "5. Split into Scenes",
                    description:
                        "Toggle AI Detection for smart scene splitting. Adjust Threshold and Min Scene Len, then click START SPLIT to segment the video.",
                    side: "top",
                },
            },
            {
                element: sel("script_analysis"),
                popover: {
                    title: "6a. Script Analysis",
                    description:
                        "View extracted transcript, narrative stages (Hook/Setup/Story/Insight/CTA/Outro), emotional tone, hook type, and CTA type.",
                    side: "bottom",
                },
            },
            {
                element: sel("audio_analysis"),
                popover: {
                    title: "6b. Audio Analysis",
                    description:
                        "Review BPM, genre, brightness, dynamic range, and time-series charts (Energy, Brightness, Flux, Onset) from the audio track.",
                    side: "bottom",
                },
            },
            {
                element: sel("visual_analysis"),
                popover: {
                    title: "6c. Visual Analysis",
                    description:
                        "Examine pacing, individual shot details (camera movement, transitions), and detected text overlay elements.",
                    side: "bottom",
                },
            },
            {
                element: sel("plan"),
                popover: {
                    title: "7. Generate Plan",
                    description:
                        "Write a brief describing your topic and requirements. AI generates a segment-by-segment plan with content slots.",
                    side: "bottom",
                },
            },
        ];

        if (planResultReady) {
            steps.push({
                element: sel("slot_segment_0"),
                popover: {
                    title: "8. Fill Slots",
                    description:
                        "For each plan segment, fill slots: type visual text or narration, upload media assets, or use AI to generate content.",
                    side: "left",
                },
            });
        }

        steps.push({
            popover: {
                title: "You're All Set!",
                description:
                    "You've toured the full pipeline: Reference → Compress → Extract → Split → Analyze → Plan → Fill. Hover dotted-underline labels for parameter tips.",
                side: "over",
            },
        });

        const d = driver({
            showProgress: true,
            progressText: "{{current}} / {{total}}",
            nextBtnText: "Next \u2192",
            prevBtnText: "\u2190 Prev",
            doneBtnText: "Done",
            showButtons: ["next", "previous", "close"],
            animate: true,
            overlayOpacity: 0.6,
            smoothScroll: true,
            steps,
            onDestroyed: () => {
                onClose();
            },
        });

        d.drive();
    }, [onClose, planResultReady]);

    return null;
}
