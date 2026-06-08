"""人声/伴奏分离 — 使用 UVR-MDX-NET 模型 + 波形相关性检测

本模块将音视频中的音轨分离为人声(vocals)和背景音乐(instrumental/BGM)两个独立轨道。

分离流程:
  1. 调用 audio-separator 库的 UVR-MDX-NET-Inst_HQ_3 模型进行频谱分离
  2. 比较分离后的两个波形皮尔逊相关系数:
     - 低相关性(差异大) → 确实分离出了人声 → 有语音
     - 高相关性(几乎相同) → UVR没找到人声，两个输出基本相同 → 纯BGM视频
  3. has_vocals 标记决定是否运行 ASR(语音转写)

为什么需要人声分离？
  - ASR 需要干净的人声轨道（背景音乐干扰会降低识别准确率）
  - BGM 分析需要纯伴奏轨道（人声干扰会影响BPM/节拍检测）
  - 迁移渲染时需要独立的 BGM 轨道（叠加新的TTS旁白）

首次运行会自动下载 ~80MB 的模型文件。
"""

import logging
from pathlib import Path

import numpy as np


def _tracks_are_different(vocals_path: str, bgm_path: str, corr_threshold: float = 0.90) -> bool:
    """检查分离后的 vocals 和 bgm 两个轨道是否有实际差异

    原理:
      UVR模型总是输出两个轨道，即使输入音频完全没有"人声+伴奏"的分离基础。
      如果输入是纯BGM(无人声)，UVR会产生两个近乎相同的副本。
      通过计算两个波形的波形皮尔逊相关系数来判断是否真的有分离效果。

    Args:
        vocals_path:   分离出的"人声"轨道文件路径
        bgm_path:      分离出的"伴奏"轨道文件路径
        corr_threshold: 相关性阈值，低于此值认为确实分离出了不同内容

    Returns:
        True  = 两个轨道差异足够大，UVR确实分离出了人声
        False = 两个轨道几乎相同，输入音频可能没有可分离的人声
    """
    try:
        import librosa

        # 加载两个音频为单声道
        yv, sr = librosa.load(vocals_path, sr=None, mono=True)  # vocals波形
        yb, _ = librosa.load(bgm_path, sr=None, mono=True)      # bgm波形

        # 对齐长度（取较短的）
        min_len = min(len(yv), len(yb))
        yv, yb = yv[:min_len], yb[:min_len]

        # 计算皮尔逊相关系数
        # corr ≈ 1.0 → 两个信号几乎相同 → 纯BGM，没分离出人声
        # corr ≈ 0.0 → 两个信号完全不同 → 成功分离出人声
        corr = float(np.corrcoef(yv, yb)[0, 1])
        return corr < corr_threshold

    except Exception:
        # 计算失败时，保守假设有差异（即认为有人声）
        return True


def separate_vocals_and_bgm(
    audio_path: str | Path,
    output_dir: str | Path,
) -> dict:
    """分离音频为人声轨道和伴奏轨道

    使用 UVR-MDX-NET-Inst_HQ_3 模型（专门针对"人声/乐器"分离训练）。
    首次运行自动下载模型(~80MB)。

    Args:
        audio_path: 输入音频文件路径（WAV格式）
        output_dir: 分离结果输出目录

    Returns:
        {
            "vocals_path": 人声文件路径(字符串),
            "bgm_path":    伴奏文件路径(字符串),
            "has_vocals":  是否检测到真人声(bool),
            "success":     分离是否成功(bool),
            "error":       错误信息(字符串，成功时为空)
        }
    """
    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not audio_path.exists():
        return {"vocals_path": "", "bgm_path": "", "has_vocals": False,
                "success": False, "error": "音频文件不存在"}

    print("  [分离] 加载 UVR-MDX-NET 人声分离模型...")

    try:
        from audio_separator.separator import Separator

        # 初始化分离器
        # output_dir: 分离结果输出目录
        # output_format: WAV无损格式（保留音频质量用于后续分析）
        # log_level: WARNING（减少冗余日志）
        separator = Separator(
            output_dir=str(output_dir),
            output_format="WAV",
            log_level=logging.WARNING,
        )

        # 加载预训练模型（首次运行自动下载）
        # UVR-MDX-NET-Inst_HQ_3: 高质量人声/乐器分离，基于MDX-NET架构
        separator.load_model("UVR-MDX-NET-Inst_HQ_3.onnx")

        # 定义输出名称映射
        # Vocals → "vocals" 文件后缀
        # Instrumental → "bgm" 文件后缀
        output_names = {
            "Vocals": "vocals",
            "Instrumental": "bgm",
        }

        print("  [分离] 正在分离人声与背景音乐...")
        output_files = separator.separate(str(audio_path), output_names)

        # 获取输出文件路径
        vocals_path = output_files[0] if len(output_files) > 0 else ""
        bgm_path = output_files[1] if len(output_files) > 1 else ""

        # 如果直接路径找不到文件，尝试在输出目录中通配搜索
        # separator 可能会给文件名追加后缀（如 _Vocals.wav）
        if not Path(vocals_path).exists() and len(output_files) >= 2:
            for f in sorted(output_dir.glob("*vocals*")):
                vocals_path = str(f)
                break
            for f in sorted(output_dir.glob("*bgm*")):
                bgm_path = str(f)
                break

        # 检测是否真的分离出了人声
        # 低相关性 → 真分离 → has_vocals=True
        # 高相关性 → 纯BGM → has_vocals=False → 跳过ASR
        has_vocals = _tracks_are_different(vocals_path, bgm_path) if (vocals_path and bgm_path) else False

        if has_vocals:
            print(f"  [分离] 完成: 检测到人声 (vocals.wav), 伴奏 (bgm.wav)")
        else:
            print(f"  [分离] 完成: 未检测到人声 (纯BGM视频), 保留伴奏 (bgm.wav)")

        return {
            "vocals_path": str(vocals_path) if vocals_path else "",
            "bgm_path": str(bgm_path) if bgm_path else "",
            "has_vocals": has_vocals,
            "success": bool(vocals_path and bgm_path),
            "error": "",
        }

    except ImportError:
        # audio-separator 未安装时的友好提示
        return {"vocals_path": "", "bgm_path": "", "has_vocals": False,
                "success": False,
                "error": "audio-separator 未安装，请运行: pip install audio-separator[cpu] onnxruntime"}
    except Exception as e:
        return {"vocals_path": "", "bgm_path": "", "has_vocals": False,
                "success": False, "error": str(e)}
