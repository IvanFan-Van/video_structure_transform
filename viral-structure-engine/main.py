"""视频结构分析引擎 — 入口脚本（main.py）

本脚本是整个分析管线的唯一入口，串联 Phase 0-4 的所有阶段。

完整管线流程:
  Phase 0: 本地预处理 — ASR语音识别、镜头切分、关键帧、BGM分析、人声分离
  Phase 1: 宏观LLM分析 — 全视频base64 + ASR → beat边界、视觉风格、脚本结构
  Phase 2: 逐beat并发LLM分析 — N个beat并发 → 文字元素、特效、转场、卖点、情绪
  Phase 3: 跨beat高层汇总 — 纯文本LLM → 卖点策略、槽位模板、素材需求
  Phase 4: 规则统计+组装 — analysis_result.json + material_template.json

运行环境要求:
  - .env 文件配置: API_KEY（火山方舟Ark）、MODEL（模型端点ID）、BASE_URL（API地址）
  - FFmpeg 已安装并在 PATH 中
  - Python 依赖已安装: pip install -r requirements.txt

用法:
  python main.py <视频绝对路径> [--output-dir output/] [--max-keyframes 20] [--max-workers 5] [--verbose]

输出:
  output/<timestamp>/
    ├── analysis_result.json     — 完整分析结果（供 transfer 使用）
    ├── material_template.json   — 用户素材填写模板
    ├── intermediates/           — 中间产物（Phase 0-3的全部数据）
    ├── keyframes/               — 关键帧JPEG图片
    └── audio/                   — 音频文件（original.wav/bgm.wav/vocals.wav）
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码（支持 emoji 输出）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import find_dotenv, load_dotenv

# 加载 .env 环境变量（API_KEY, BASE_URL, MODEL）
load_dotenv(find_dotenv(), override=True)

# 环境变量校验
if not os.getenv("API_KEY") or not os.getenv("BASE_URL") or not os.getenv("MODEL"):
    print("错误: 请在 .env 文件中设置 API_KEY, BASE_URL, MODEL")
    sys.exit(1)

# 导入分析管线的核心模块
from analysis.preprocess import preprocess                           # Phase 0: 本地预处理
from analysis.analyzer import (                                      # Phase 1/2/3: LLM分析
    analyze_phase1_full_video,   # Phase 1: 全视频宏观分析（1次LLM）
    analyze_phase2_per_beats,    # Phase 2: 逐beat并发分析（N次LLM）
    analyze_phase3_summary,      # Phase 3: 跨beat高层汇总（1次LLM）
    postprocess_beats,           # Beat后处理（切点吸附/间隙填充/短beat合并）
    save_intermediate_result,    # 保存中间结果
)
from analysis.assembler import assemble_final_output, save_final_output  # Phase 4: 最终组装


def main():
    """主函数 — 解析命令行参数并驱动整个分析管线"""
    # ── 命令行参数解析 ──
    parser = argparse.ArgumentParser(
        description="视频结构分析引擎 — 4阶段深度分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py S:\\videos\\example.mp4
  python main.py C:\\Users\\me\\video.mp4 --output-dir ./my_output --max-keyframes 10
  python main.py /path/to/video.mp4 --verbose
        """,
    )
    parser.add_argument("video_path", type=str, help="视频文件的绝对路径")
    parser.add_argument("--output-dir", type=str, default="output", help="输出目录 (默认: output/)")
    parser.add_argument("--max-keyframes", type=int, default=20, help="阶段0最大关键帧数量 (默认: 20)")
    parser.add_argument("--max-workers", type=int, default=5, help="阶段2并发数 (默认: 5)")
    parser.add_argument("--verbose", action="store_true", help="打印详细中间结果")
    args = parser.parse_args()

    # ── 输入验证 ──
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"错误: 视频文件不存在: {video_path}")
        sys.exit(1)

    # 输出目录: output/<时间戳>/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_dir) / timestamp

    # ── 打印配置信息 ──
    print("=" * 70)
    print("  爆款结构迁移引擎 — 视频结构分析 v2.0")
    print("=" * 70)
    print(f"  输入: {video_path}")
    print(f"  输出: {run_dir}")
    print(f"  模型: {os.getenv('MODEL')}")
    print(f"  API:  {os.getenv('BASE_URL')}")
    print(f"  阶段: 0预处理 → 1宏观LLM → 2逐beat并发LLM → 3汇总")
    print("=" * 70)

    total_start = time.time()

    # ══════════════════════════════════════════════════════════════
    # Phase 0: 本地预处理
    #   - ffprobe 提取视频元数据（时长、分辨率、帧率）
    #   - ffmpeg 提取音频 → UVR-MDX-NET 分离人声+BGM
    #   - faster-whisper ASR 词级时间戳转写
    #   - OpenCV 直方图差异法镜头切分
    #   - 关键帧抽取（每个镜头中点 + 首尾帧）
    #   - librosa BPM检测 + 节拍追踪 + 能量曲线
    #   - 卡点同步率计算（切点 vs 重拍距离<50ms）
    # ══════════════════════════════════════════════════════════════
    result = preprocess(str(video_path), str(run_dir), args.max_keyframes)

    # ══════════════════════════════════════════════════════════════
    # Phase 1: 全视频宏观分析（1次LLM调用）
    #   输入: 完整视频base64 + ASR词级时间戳 + BGM数据 + 切点参考
    #   输出: beat边界、视觉风格分类、脚本结构（hook/pain_point/solution/cta等）
    # ══════════════════════════════════════════════════════════════
    phase1 = analyze_phase1_full_video(str(video_path), result)
    save_intermediate_result(phase1, "phase1_macro.json", run_dir)

    if args.verbose:
        print("\n[详细] Phase 1 输出:")
        print(json.dumps(phase1, ensure_ascii=False, indent=2)[:2000])

    # ── Beat 后处理: 吸附切点 → 修正首尾 → 填充间隙 → 合并短beat ──
    raw_beats = phase1.get("beats", [])
    if raw_beats:
        raw_beats = postprocess_beats(
            raw_beats,
            result.shot_boundaries,  # cv2检测的镜头切点
            result.duration,         # 视频总时长
            result.fps,              # 帧率
        )
        print(
            f"  Beats 后处理完成: {len(raw_beats)} 个 (原始 {len(phase1.get('beats', []))} 个)"
        )

    # ══════════════════════════════════════════════════════════════
    # Phase 2: 逐 Beat 精细分析（N次并发LLM调用）
    #   每个beat独立发送: 视频片段(base64) + 8帧密集关键帧 + ASR词级时间戳
    #   并发数由 --max-workers 控制（默认5）
    #   产出: 文字元素(text/font_size/position)、视觉特效(含remocn组件名)、
    #         转场类型、剪辑手法、卖点内容、情绪标签
    # ══════════════════════════════════════════════════════════════
    phase2_beats = analyze_phase2_per_beats(
        raw_beats,
        str(video_path),
        result,
        run_dir,
        max_workers=args.max_workers,
    )

    # 保存每个 beat 的独立分析结果（调试用）
    beat_out_dir = Path(run_dir) / "intermediates" / "beats"
    beat_out_dir.mkdir(parents=True, exist_ok=True)
    for b in phase2_beats:
        bid = b.get("beat_id", 0)
        with open(beat_out_dir / f"beat_{bid:02d}.json", "w", encoding="utf-8") as f:
            json.dump(b, f, ensure_ascii=False, indent=2)

    save_intermediate_result(
        {"beats": phase2_beats}, "phase2_beats_summary.json", run_dir
    )

    if args.verbose:
        print(f"\n[详细] Phase 2: {len(phase2_beats)} 个 beat 完成")

    # ══════════════════════════════════════════════════════════════
    # Phase 3: 跨 Beat 高层汇总（1次LLM调用，纯文本，不下发视频）
    #   输入: 所有beat的压缩摘要 + 脚本结构 + BGM特征
    #   输出: 卖点策略分析(递进式/并列式)、结构槽位模板(含{占位符})、
    #         素材需求清单(标注是否可AIGC生成)
    # ══════════════════════════════════════════════════════════════
    phase3 = analyze_phase3_summary(result, phase1, phase2_beats)
    save_intermediate_result(phase3, "phase3_summary.json", run_dir)

    if args.verbose:
        print("\n[详细] Phase 3 输出:")
        print(json.dumps(phase3, ensure_ascii=False, indent=2)[:2000])

    # ══════════════════════════════════════════════════════════════
    # Phase 4: 组装最终输出（纯代码规则，不含LLM）
    #   规则统计: 卖点汇总 / 转场分布 / 包装主导类型 / 节奏结构 / 缺口分析
    #   产出: analysis_result.json（供 transfer 迁移使用）
    # ══════════════════════════════════════════════════════════════
    final_output = assemble_final_output(result, phase1, phase2_beats, phase3)
    output_path = save_final_output(final_output, run_dir)

    # ══════════════════════════════════════════════════════════════
    # 生成素材清单模板 — 用户填完即可用于 transfer
    # ══════════════════════════════════════════════════════════════
    from analysis.generate_material_template import generate as generate_template

    template_path = generate_template(str(output_path), str(run_dir))
    print(f"📋 素材清单: {template_path}")

    # ══════════════════════════════════════════════════════════════
    # 摘要 — 打印分析结果概览
    # ══════════════════════════════════════════════════════════════
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print("  分析完成!")
    print(f"  总耗时: {total_elapsed:.1f}s")
    print(f"  输出文件: {output_path}")
    print("=" * 70)
    print()
    print("📊 分析结果概览:")
    print(f"  脚本段落: {len(final_output.get('script_structure', []))} 段")
    print(f"  Beat 分析: {len(final_output.get('beats', []))} 个")
    print(f"  结构槽位: {len(final_output.get('slot_template', []))} 个")
    print(f"  卖点提取: {len(final_output.get('selling_points', []))} 个")
    print(f"  素材缺口: {len(final_output.get('gap_analysis', []))} 项")
    print(
        f"  卡点匹配率: {final_output.get('bgm_features', {}).get('beat_alignments', {}).get('match_rate', 0):.1%}"
    )
    print()
    print(f"📝 摘要: {final_output.get('_summary', '')}")
    print()

    # 打印素材缺口列表
    gaps = final_output.get("gap_analysis", [])
    if gaps:
        print("⚠️  素材缺口:")
        for g in gaps:
            imp = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                g.get("impact", ""), "⚪"
            )
            print(
                f"  {imp} 槽位{g.get('slot_id', '?')} [{g.get('label', '?')}]: "
                f"缺 {g.get('missing_type', '?')} — {g.get('alternative_if_missing', '')[:60]}"
            )

    # 打印卖点清单
    sps = final_output.get("selling_points", [])
    if sps:
        print(f"\n💡 卖点清单 ({len(sps)} 个):")
        for sp in sps:
            print(
                f"  [{sp.get('time', 0):.1f}s] [{sp.get('strategy', '?')}] {sp.get('text', '')[:60]}"
            )


if __name__ == "__main__":
    main()
