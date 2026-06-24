"""音频处理工具函数"""

import subprocess


def convert_to_wav(input_path: str) -> str:
    """将任意音频格式转为 16kHz 单声道 WAV"""
    output_path = input_path + "_converted.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path,
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
         output_path],
        check=True, capture_output=True,
    )
    return output_path