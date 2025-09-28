"""
動画ファイル解析・検索モジュール
"""

import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from ..core.config import Config
from ..core.models import VideoFile


class VideoFileParser:
    """動画ファイルの解析・検索を行うクラス"""

    def __init__(self, config: Config):
        """
        初期化

        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.video_pattern = re.compile(config.video_pattern)

    def parse_filename(self, filename: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        ファイル名から日付、時刻、連番、カメラ位置を抽出

        Args:
            filename: ファイル名

        Returns:
            (日付, 時刻, 連番, カメラ位置) のタプル、解析失敗時は(None, None, None, None)

        Examples:
            >>> parser.parse_filename("NO20250906-134056-000895F.MP4")
            ("20250906", "134056", "000895", "F")
        """
        match = self.video_pattern.match(filename)
        if match:
            date_str, time_str, sequence, camera_pos = match.groups()
            return date_str, time_str, sequence, camera_pos
        return None, None, None, None

    def find_video_files(self) -> Dict[str, Dict[str, List[VideoFile]]]:
        """
        設定されたカメラパスから動画ファイルを取得し、日付・カメラ位置ごとにグループ化

        Returns:
            {日付: {カメラ位置: [VideoFileリスト]}} の辞書
        """
        videos_by_date_camera = defaultdict(lambda: defaultdict(list))

        # 各カメラパスからファイルを取得
        for camera_pos, camera_path in self.config.camera_paths.items():
            if not camera_path.exists():
                print(f"警告: カメラ {camera_pos} のパスが見つかりません: {camera_path}")
                continue

            for file_path in camera_path.glob("*.MP4"):
                date_str, time_str, sequence, file_camera_pos = self.parse_filename(file_path.name)
                if date_str and file_camera_pos == camera_pos:
                    video_file = VideoFile(
                        path=file_path,
                        date=date_str,
                        time=time_str,
                        sequence=sequence,
                        camera_pos=camera_pos,
                        filename=file_path.name
                    )
                    videos_by_date_camera[date_str][camera_pos].append(video_file)

        # 各日付・カメラ位置のファイルを時刻順にソート
        for date_str in videos_by_date_camera:
            for camera_pos in videos_by_date_camera[date_str]:
                videos_by_date_camera[date_str][camera_pos].sort(
                    key=lambda x: (x.time, x.sequence)
                )

        return videos_by_date_camera

    def filter_by_date(self, videos_by_date_camera: Dict[str, Dict[str, List[VideoFile]]],
                      target_date: str) -> Dict[str, Dict[str, List[VideoFile]]]:
        """
        特定の日付でフィルタリング

        Args:
            videos_by_date_camera: 日付・カメラ別の動画ファイル辞書
            target_date: 対象日付（YYYYMMDD形式）

        Returns:
            フィルタリング後の辞書
        """
        if target_date in videos_by_date_camera:
            return {target_date: videos_by_date_camera[target_date]}
        return {}

    def get_video_info(self, video_files: List[VideoFile]) -> Dict[str, any]:
        """
        動画ファイル群の情報を取得

        Args:
            video_files: VideoFileのリスト

        Returns:
            ファイル情報の辞書
        """
        if not video_files:
            return {}

        first_file = video_files[0]
        last_file = video_files[-1]
        total_size = sum(video.size_mb for video in video_files)

        return {
            'start_time': first_file.formatted_time,
            'end_time': last_file.formatted_time,
            'file_count': len(video_files),
            'total_size_mb': total_size
        }