"""音频处理工具函数"""

import subprocess
import os

# ffmpeg 候选路径（Windows 下常见安装位置）
_FFMPEG_PATHS = [
    "ffmpeg",                                    # 系统 PATH
    "/d/dwrg/ffmpeg/ffmpeg.exe",                 # 本地工具
    "/d/FeverApps/dwrg2/ffmpeg/ffmpeg.exe",
]


def _find_ffmpeg() -> str:
    """查找可用的 ffmpeg 路径"""
    for path in _FFMPEG_PATHS:
        if os.path.isfile(path) or path == "ffmpeg":
            try:
                subprocess.run([path, "-version"], capture_output=True, timeout=5)
                return path
            except Exception:
                continue
    raise FileNotFoundError("ffmpeg 未找到")


def convert_to_wav(input_path: str) -> str:
    """将任意音频格式转为 16kHz 单声道 WAV

    如果输入已是 WAV 格式（16kHz mono），直接返回原路径。
    否则使用 ffmpeg 转码。
    """
    # 检查是否已是 WAV（通过文件头判断）
    try:
        with open(input_path, 'rb') as f:
            header = f.read(12)
            if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                return input_path  # 已是 WAV 格式，无需转码
    except Exception:
        pass

    output_path = input_path + "_converted.wav"
    try:
        ffmpeg = _find_ffmpeg()
        subprocess.run(
            [ffmpeg, "-y", "-i", input_path,
             "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
             output_path],
            check=True, capture_output=True, timeout=30,
        )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg 未安装，请安装 ffmpeg 后重试。下载地址: https://ffmpeg.org/download.html")
    return output_path