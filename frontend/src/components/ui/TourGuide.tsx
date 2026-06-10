import { useEffect, useRef } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";
import type { DriveStep } from "driver.js";
import { useCanvasStore } from "../../store/useCanvasStore";

interface Props {
    onClose: () => void;
    planResultReady: boolean;
    lang: "en" | "zh";
}

function sel(id: string) {
    return `[data-tour="${id}"]`;
}

type StepText = { title: string; description: string };

const I18N: Record<string, { en: StepText; zh: StepText }> = {
    reference: {
        en: {
            title: "1. Upload Reference Video",
            description:
                "Drag and drop or click to upload a viral video you want to analyze. Supported formats: .mp4 .mov .avi .mkv .webm",
        },
        zh: {
            title: "1. 上传参考视频",
            description:
                "拖拽或点击上传你想要分析的短视频。支持格式：.mp4 .mov .avi .mkv .webm",
        },
    },
    compress_config: {
        en: {
            title: "2. Configure Compression",
            description:
                "Set video codec, quality (CRF), resolution, frame rate, and audio codec. These determine the output video specs used in later steps.",
        },
        zh: {
            title: "2. 配置压缩参数",
            description:
                "设置视频编码器、质量(CRF)、分辨率、帧率和音频编码器。这些决定后续步骤使用的视频规格。",
        },
    },
    compress: {
        en: {
            title: "3. Compress Video",
            description:
                "Click COMPRESS to transcode the video. A before/after comparison will show the size savings.",
        },
        zh: {
            title: "3. 压缩视频",
            description:
                "点击 COMPRESS 转码视频。压缩前后对比会显示体积节省。",
        },
    },
    extracting: {
        en: {
            title: "4. Extract Analysis Data",
            description:
                "Run three parallel analyses: Script Structure (transcript + narrative stages), BGM Features (tempo/genre), and Video Features (shots/camera/transitions).",
        },
        zh: {
            title: "4. 提取分析数据",
            description:
                "并行运行三项分析：脚本结构（文本+叙事阶段）、BGM特征（节奏/流派）、视频特征（镜头/运镜/转场）。",
        },
    },
    split: {
        en: {
            title: "5. Split into Scenes",
            description:
                "Toggle AI Detection for smart scene splitting. Adjust Threshold and Min Scene Len, then click START SPLIT to segment the video.",
        },
        zh: {
            title: "5. 切割场景",
            description:
                "切换 AI Detection 进行智能场景切割。调整 Threshold 和 Min Scene Len 参数，点击 START SPLIT 切割视频。",
        },
    },
    script_analysis: {
        en: {
            title: "6a. Script Analysis",
            description:
                "View extracted transcript, narrative stages (Hook/Setup/Story/Insight/CTA/Outro), emotional tone, hook type, and CTA type.",
        },
        zh: {
            title: "6a. 脚本分析",
            description:
                "查看提取的文本、叙事阶段（钩子/铺垫/正文/金句/CTA/结尾）、情绪基调、钩子类型和 CTA 类型。",
        },
    },
    audio_analysis: {
        en: {
            title: "6b. Audio Analysis",
            description:
                "Review BPM, genre, brightness, dynamic range, and time-series charts (Energy, Brightness, Flux, Onset) from the audio track.",
        },
        zh: {
            title: "6b. 音频分析",
            description:
                "查看 BPM、流派、亮度、动态范围，以及时间序列图表（能量、亮度、频谱通量、音符起始）等音频特征。",
        },
    },
    visual_analysis: {
        en: {
            title: "6c. Visual Analysis",
            description:
                "Examine pacing, individual shot details (camera movement, transitions), and detected text overlay elements.",
        },
        zh: {
            title: "6c. 视觉分析",
            description:
                "查看节奏、各镜头详情（运镜方式、转场类型）以及检测到的文字叠层元素。",
        },
    },
    plan: {
        en: {
            title: "7. Generate Plan",
            description:
                "Write a brief describing your topic and requirements. AI generates a segment-by-segment plan with content slots.",
        },
        zh: {
            title: "7. 生成计划",
            description:
                "撰写 Brief 描述你的主题和需求。AI 逐段生成包含内容槽位的完整计划。",
        },
    },
    plan_generate: {
        en: {
            title: "9. Batch Generate Slot Content",
            description:
                "AI generates all pending slots in one batch. Review pending summary grouped by type and segment, then click Generate All.",
        },
        zh: {
            title: "9. 批量生成槽位内容",
            description:
                "AI 一次性生成所有待处理槽位。按类型和分段查看待生成摘要，点击 Generate All 批量生成。",
        },
    },
    render: {
        en: {
            title: "10. Render Final Video",
            description:
                "Renders the plan into an MP4 video. Shows render progress phase-by-phase (loading, BGM, building, rendering, saving).",
        },
        zh: {
            title: "10. 渲染最终视频",
            description:
                "将 Plan 渲染为 MP4 视频。分阶段展示进度（加载数据、BGM音频、构建配置、逐帧渲染、保存输出）。",
        },
    },
    slot: {
        en: {
            title: "8. Fill Slots",
            description:
                "For each plan segment, fill slots: type visual text or narration, upload media assets, or use AI to generate content.",
        },
        zh: {
            title: "8. 填充槽位",
            description:
                "为每个 Plan 分段填充槽位：输入画面文字或旁白、上传媒体素材、或使用 AI 生成内容。",
        },
    },
    done: {
        en: {
            title: "You're All Set!",
            description:
                "You've toured the full pipeline: Reference → Compress → Extract → Split → Analyze → Plan → Fill → Generate → Render. Hover dotted-underline labels for parameter tips.",
        },
        zh: {
            title: "探索完成！",
            description:
                "你已浏览完整流水线：上传 → 压缩 → 提取 → 切割 → 分析 → 计划 → 填充 → 生成 → 渲染。悬停虚线下划线标签查看参数提示。",
        },
    },
};

function t(key: string, lang: "en" | "zh"): StepText {
    return I18N[key]?.[lang] ?? I18N[key]?.en ?? { title: key, description: "" };
}

export function TourGuide({ onClose, planResultReady, lang }: Props) {
    const driverRef = useRef<ReturnType<typeof driver> | null>(null);

    const buildSteps = (): DriveStep[] => {
        const steps: DriveStep[] = [
            {
                element: sel("reference"),
                popover: { ...t("reference", lang), side: "bottom" },
            },
            {
                element: sel("compress_config"),
                popover: { ...t("compress_config", lang), side: "bottom" },
            },
            {
                element: sel("compress"),
                popover: { ...t("compress", lang), side: "bottom" },
            },
            {
                element: sel("extracting"),
                popover: { ...t("extracting", lang), side: "bottom" },
            },
            {
                element: sel("split"),
                popover: { ...t("split", lang), side: "top" },
            },
            {
                element: sel("script_analysis"),
                popover: { ...t("script_analysis", lang), side: "bottom" },
            },
            {
                element: sel("audio_analysis"),
                popover: { ...t("audio_analysis", lang), side: "bottom" },
            },
            {
                element: sel("visual_analysis"),
                popover: { ...t("visual_analysis", lang), side: "bottom" },
            },
            {
                element: sel("plan"),
                popover: { ...t("plan", lang), side: "bottom" },
            },
        ];

        if (planResultReady) {
            steps.push({
                element: sel("slot_segment_0"),
                popover: { ...t("slot", lang), side: "left" },
            });
            steps.push({
                element: sel("plan_generate"),
                popover: { ...t("plan_generate", lang), side: "left" },
            });
        }

        steps.push({
            element: sel("render"),
            popover: { ...t("render", lang), side: "left" },
        });

        steps.push({
            popover: { ...t("done", lang), side: "over" },
        });

        return steps;
    };

    useEffect(() => {
        // Save current canvas state and reset for tour
        const canvas = useCanvasStore.getState();
        const savedView = {
            zoom: canvas.zoom,
            panX: canvas.panX,
            panY: canvas.panY,
        };
        canvas.setZoom(() => 0.5);
        canvas.setPan(() => ({ x: 0, y: 0 }));

        const steps = buildSteps();

        const btnText =
            lang === "zh"
                ? { next: "下一步 \u2192", prev: "\u2190 上一步", done: "完成" }
                : { next: "Next \u2192", prev: "\u2190 Prev", done: "Done" };

        const d = driver({
            showProgress: true,
            progressText: "{{current}} / {{total}}",
            nextBtnText: btnText.next,
            prevBtnText: btnText.prev,
            doneBtnText: btnText.done,
            showButtons: ["next", "previous", "close"],
            animate: true,
            overlayOpacity: 0.6,
            smoothScroll: true,
            steps,
            onDestroyed: () => {
                const s = useCanvasStore.getState();
                s.setZoom(() => savedView.zoom);
                s.setPan(() => ({ x: savedView.panX, y: savedView.panY }));
                onClose();
            },
        });

        driverRef.current = d;
        d.drive();

        return () => {
            driverRef.current?.destroy();
            driverRef.current = null;
        };
    }, [lang]);

    return null;
}
