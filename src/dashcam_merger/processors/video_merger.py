"""
動画マージ処理モジュール
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

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

    def create_file_list(self, video_files: List[VideoFile], date_str: str, camera_pos: str, use_local_temp: bool = True) -> Path:
        """
        FFmpegで使用するファイルリストを作成

        Args:
            video_files: マージする動画ファイルのリスト
            date_str: 日付文字列
            camera_pos: カメラ位置
            use_local_temp: ローカル一時ディレクトリを使用するかどうか

        Returns:
            作成されたファイルリストのパス
        """
        if use_local_temp:
            # ローカル一時ディレクトリにファイルリストを作成（NAS環境での高速化）
            temp_dir = Path(tempfile.gettempdir())
            list_file_path = temp_dir / f"filelist_{date_str}_{camera_pos}.txt"
        else:
            # 従来通り出力ディレクトリに作成
            list_file_path = self.config.output_dir / f"filelist_{date_str}_{camera_pos}.txt"

        with open(list_file_path, 'w', encoding='utf-8') as f:
            for video in video_files:
                # FFmpegのconcatフィルター用のフォーマット
                f.write(f"file '{video.path.absolute()}'\n")

        return list_file_path

    def merge_videos(self, video_files: List[VideoFile], date_str: str, camera_pos: str, use_local_processing: bool = True) -> bool:
        """
        指定された動画ファイルをマージ

        Args:
            video_files: マージする動画ファイルのリスト
            date_str: 日付文字列
            camera_pos: カメラ位置
            use_local_processing: ローカル処理を使用するかどうか（NAS環境での高速化）

        Returns:
            マージ成功時True、失敗時False
        """
        if not video_files:
            print(f"日付 {date_str} カメラ {camera_pos} の動画ファイルが見つかりませんでした")
            return False

        camera_name = self.config.get_camera_name(camera_pos)
        print(f"日付 {date_str} {camera_name}カメラ: {len(video_files)} 個のファイルをマージ中...")

        # ファイルリストを作成（ローカル一時ディレクトリ使用）
        list_file = self.create_file_list(video_files, date_str, camera_pos, use_local_temp=use_local_processing)

        # 出力ファイル名を生成
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        final_output_file = self.config.output_dir / f"merged_{formatted_date}_{camera_pos}.mp4"

        # ローカル処理の場合、一時出力ファイルを使用
        if use_local_processing:
            temp_dir = Path(tempfile.gettempdir())
            temp_output_file = temp_dir / f"merged_{formatted_date}_{camera_pos}.mp4"
        else:
            temp_output_file = final_output_file

        success = False

        # ストリームコピーを試行
        if self._try_stream_copy_optimized(list_file, temp_output_file):
            success = True
        else:
            # 再エンコードを試行
            success = self._try_reencode_optimized(list_file, temp_output_file)

        # ローカル処理の場合、最終出力先に移動
        if success and use_local_processing and temp_output_file != final_output_file:
            try:
                print(f"処理完了ファイルをNASに移動中: {final_output_file}")
                shutil.move(str(temp_output_file), str(final_output_file))
                print(f"マージ完了: {final_output_file}")
            except Exception as e:
                print(f"ファイル移動エラー: {e}")
                success = False

        # 一時ファイルをクリーンアップ
        self._cleanup_temp_file(list_file)
        if use_local_processing and temp_output_file.exists() and temp_output_file != final_output_file:
            self._cleanup_temp_file(temp_output_file)

        return success

    def _try_stream_copy_optimized(self, list_file: Path, output_file: Path) -> bool:
        """
        ストリームコピーでマージを試行（NAS最適化版）

        Args:
            list_file: ファイルリストのパス
            output_file: 出力ファイルのパス

        Returns:
            成功時True、失敗時False
        """
        copy_settings = self.config.ffmpeg_copy_settings
        cmd = [
            'ffmpeg',
            # ネットワーク読み込み最適化オプション
            '-probesize', '32M',
            '-analyzeduration', '10M',
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
            if output_file.parent != self.config.output_dir:
                print(f"ローカル処理完了: {output_file}")
            else:
                print(f"マージ完了: {output_file}")
            return True
        except subprocess.CalledProcessError:
            print(f"ストリームコピーに失敗。再エンコードを試行中...")
            return False
        except FileNotFoundError:
            print("FFmpegが見つかりません。FFmpegをインストールしてください。")
            return False

    def _try_reencode_optimized(self, list_file: Path, output_file: Path) -> bool:
        """
        再エンコードでマージを試行（NAS最適化版）

        Args:
            list_file: ファイルリストのパス
            output_file: 出力ファイルのパス

        Returns:
            成功時True、失敗時False
        """
        reencode_settings = self.config.ffmpeg_reencode_settings
        cmd = [
            'ffmpeg',
            # ネットワーク読み込み最適化オプション
            '-probesize', '32M',
            '-analyzeduration', '10M',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c:v', reencode_settings["video_codec"],
            '-c:a', reencode_settings["audio_codec"],
            '-preset', reencode_settings["preset"],
            '-crf', reencode_settings["crf"],
            '-avoid_negative_ts', 'make_zero',
            # スレッド数最適化（CPUコア数に応じて調整）
            '-threads', '0',
            '-y',
            str(output_file)
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            if output_file.parent != self.config.output_dir:
                print(f"再エンコード処理完了: {output_file}")
            else:
                print(f"再エンコードでマージ完了: {output_file}")
            return True
        except subprocess.CalledProcessError:
            # ファイルが作成されているかチェック
            if output_file.exists() and output_file.stat().st_size > 0:
                print(f"警告: エラーが発生しましたが、動画ファイルは作成されました: {output_file}")
                print(f"ファイルサイズ: {output_file.stat().st_size / (1024*1024):.1f} MB")
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