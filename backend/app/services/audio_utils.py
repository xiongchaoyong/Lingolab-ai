"""音频处理工具函数"""

import os
import subprocess
import shutil


def _find_ffmpeg() -> str:
    """查找 ffmpeg 可执行文件路径，找不到则回退到 'ffmpeg'"""
    # 1. 先尝试 shell 自带的
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 2. Windows 常见安装路径
    candidates = [
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ]
    # winget 安装路径（模糊匹配）
    winget_base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if os.path.isdir(winget_base):
        for name in os.listdir(winget_base):
            if name.lower().startswith("gyan.ffmpeg"):
                ffmpeg_path = os.path.join(winget_base, name, "ffmpeg-*-full_build", "bin", "ffmpeg.exe")
                import glob
                matches = glob.glob(ffmpeg_path)
                if matches:
                    return matches[0]
                # 尝试直接遍历找
                for root, dirs, files in os.walk(os.path.join(winget_base, name)):
                    if "ffmpeg.exe" in files:
                        return os.path.join(root, "ffmpeg.exe")

    for path in candidates:
        if os.path.isfile(path):
            return path

    return "ffmpeg"  # 最后回退


def convert_to_wav(input_path: str) -> str:
    """将任意音频格式转为 16kHz 单声道 WAV"""
    ffmpeg = _find_ffmpeg()
    output_path = input_path + "_converted.wav"
    subprocess.run(
        [ffmpeg, "-y", "-i", input_path,
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
         output_path],
        check=True, capture_output=True,
    )
    return output_path