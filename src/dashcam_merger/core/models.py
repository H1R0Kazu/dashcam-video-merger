"""
データモデル定義
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoFile:
    """動画ファイル情報を格納するデータクラス"""
    path: Path
    date: str
    time: str
    sequence: str
    camera_pos: str
    filename: str

    @property
    def size_mb(self) -> float:
        """ファイルサイズをMBで取得"""
        return self.path.stat().st_size / (1024 * 1024)

    @property
    def formatted_time(self) -> str:
        """時刻を HH:MM:SS 形式で取得"""
        return f"{self.time[:2]}:{self.time[2:4]}:{self.time[4:6]}"

    @property
    def formatted_date(self) -> str:
        """日付を YYYY-MM-DD 形式で取得"""
        return f"{self.date[:4]}-{self.date[4:6]}-{self.date[6:8]}"

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.formatted_date} {self.formatted_time} [{self.camera_pos}] {self.filename}"