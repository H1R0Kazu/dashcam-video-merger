"""
動画マージ処理モジュール
"""

import subprocess
from pathlib import Path
from typing import List

from ..core.config import Config
from ..core.models import VideoFile


class VideoMerger:
    """FFmpegを使用した動画マージ処理を行うクラス"""

    def __init__(self, config: Config):
        """
        初期化

        Args:
            config: 設定オブジェクト
        """
        self.config = config

    def create_file_list(self, video_files: List[VideoFile], date_str: str, camera_pos: str) -> Path:
        """
        FFmpegで使用するファイルリストを作成

        Args:
            video_files: マージする動画ファイルのリスト
            date_str: 日付文字列
            camera_pos: カメラ位置

        Returns:
            作成されたファイルリストのパス
        """
        list_file_path = self.config.output_dir / f"filelist_{date_str}_{camera_pos}.txt"

        with open(list_file_path, 'w', encoding='utf-8') as f:
            for video in video_files:
                # FFmpegのconcatフィルター用のフォーマット
                f.write(f"file '{video.path.absolute()}'\n")

        return list_file_path

    def merge_videos(self, video_files: List[VideoFile], date_str: str, camera_pos: str) -> bool:
        """
        指定された動画ファイルをマージ

        Args:
            video_files: マージする動画ファイルのリスト
            date_str: 日付文字列
            camera_pos: カメラ位置

        Returns:
            マージ成功時True、失敗時False
        """
        if not video_files:
            print(f"日付 {date_str} カメラ {camera_pos} の動画ファイルが見つかりませんでした")
            return False

        camera_name = self.config.get_camera_name(camera_pos)
        print(f"日付 {date_str} {camera_name}カメラ: {len(video_files)} 個のファイルをマージ中...")

        # ファイルリストを作成
        list_file = self.create_file_list(video_files, date_str, camera_pos)

        # 出力ファイル名を生成（日付を読みやすい形式に変換）
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        output_file = self.config.output_dir / f"merged_{formatted_date}_{camera_pos}.mp4"

        # ストリームコピーを試行
        if self._try_stream_copy(list_file, output_file):
            self._cleanup_temp_file(list_file)
            return True

        # 再エンコードを試行
        return self._try_reencode(list_file, output_file)

    def _try_stream_copy(self, list_file: Path, output_file: Path) -> bool:
        """
        ストリームコピーでマージを試行

        Args:
            list_file: ファイルリストのパス
            output_file: 出力ファイルのパス

        Returns:
            成功時True、失敗時False
        """
        copy_settings = self.config.ffmpeg_copy_settings
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c:v', copy_settings["video"],
            '-c:a', copy_settings["audio"],
            '-avoid_negative_ts', 'make_zero',
            '-fflags', '+genpts',
            '-y',
            str(output_file)
        ]

        try:
            print(f"ストリームコピーでマージを試行中...")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"マージ完了: {output_file}")
            return True
        except subprocess.CalledProcessError:
            print(f"ストリームコピーに失敗。再エンコードを試行中...")
            return False
        except FileNotFoundError:
            print("FFmpegが見つかりません。FFmpegをインストールしてください。")
            return False

    def _try_reencode(self, list_file: Path, output_file: Path) -> bool:
        """
        再エンコードでマージを試行

        Args:
            list_file: ファイルリストのパス
            output_file: 出力ファイルのパス

        Returns:
            成功時True、失敗時False
        """
        reencode_settings = self.config.ffmpeg_reencode_settings
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c:v', reencode_settings["video_codec"],
            '-c:a', reencode_settings["audio_codec"],
            '-preset', reencode_settings["preset"],
            '-crf', reencode_settings["crf"],
            '-avoid_negative_ts', 'make_zero',
            '-y',
            str(output_file)
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"再エンコードでマージ完了: {output_file}")
            self._cleanup_temp_file(list_file)
            return True
        except subprocess.CalledProcessError:
            # ファイルが作成されているかチェック
            if output_file.exists() and output_file.stat().st_size > 0:
                print(f"警告: エラーが発生しましたが、動画ファイルは作成されました: {output_file}")
                print(f"ファイルサイズ: {output_file.stat().st_size / (1024*1024):.1f} MB")
                self._cleanup_temp_file(list_file)
                return True
            else:
                print(f"再エンコードも失敗しました")
                return False

    def _cleanup_temp_file(self, list_file: Path):
        """
        一時ファイルを削除

        Args:
            list_file: 削除するファイルのパス
        """
        try:
            list_file.unlink()
        except OSError:
            pass  # 一時ファイルの削除に失敗しても続行