"""
Core module for dashcam video merger.
Contains configuration management and data models.
"""

from .config import Config
from .models import VideoFile

__all__ = ["Config", "VideoFile"]