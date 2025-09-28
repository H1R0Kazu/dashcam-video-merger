"""
Dashcam Video Merger

ドライブレコーダーの細切れ動画を日付・カメラ別にマージするPythonパッケージ
"""

from .core import Config, VideoFile
from .parsers import VideoFileParser
from .processors import VideoMerger
from .cli import DashcamVideoMergerApp, main

__version__ = "1.0.0"
__author__ = "H1R0Kazu"

__all__ = [
    "Config",
    "VideoFile",
    "VideoFileParser",
    "VideoMerger",
    "DashcamVideoMergerApp",
    "main"
]