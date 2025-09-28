#!/usr/bin/env python3
"""
ドライブレコーダーの細切れ動画を日付ごとに1つの動画にマージするプログラム

使用方法:
    python -m dashcam_merger -d 20250906  # 特定日付のみ
    python -m dashcam_merger              # 全日付
    python -m dashcam_merger -c config.json --no-info  # カスタム設定、詳細非表示
"""

import argparse
import sys
from pathlib import Path

from ..core.config import Config
from ..parsers.file_parser import VideoFileParser
from ..processors.video_merger import VideoMerger


class DashcamVideoMergerApp:
    """ドライブレコーダー動画マージアプリケーション"""

    def __init__(self, config_path: str = None):
        """
        初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config = Config(config_path)
        self.config.ensure_output_dir()

        self.file_parser = VideoFileParser(self.config)
        self.video_merger = VideoMerger(self.config)

    def display_config_info(self):
        """設定情報を表示"""
        print(f"設定されたカメラパス:")
        for camera_pos, camera_path in self.config.camera_paths.items():
            camera_name = self.config.get_camera_name(camera_pos)
            print(f"  {camera_name}カメラ ({camera_pos}): {camera_path}")
        print(f"出力ディレクトリ: {self.config.output_dir}")

    def display_video_info(self, video_files, camera_name):
        """動画ファイル情報を表示"""
        info = self.file_parser.get_video_info(video_files)
        if info:
            print(f"  開始時刻: {info['start_time']}")
            print(f"  終了時刻: {info['end_time']}")
            print(f"  ファイル数: {info['file_count']}")
            print(f"  総サイズ: {info['total_size_mb']:.1f} MB")

    def merge_all(self, show_info: bool = True, target_date: str = None):
        """
        すべての日付の動画をマージ

        Args:
            show_info: ファイル情報を表示するかどうか
            target_date: 特定の日付のみを処理する場合の日付（YYYYMMDD形式）
        """
        # 動画ファイルを検索・グループ化
        videos_by_date_camera = self.file_parser.find_video_files()

        if not videos_by_date_camera:
            print("マージ対象の動画ファイルが見つかりませんでした")
            return

        # 設定情報を表示
        self.display_config_info()

        # 特定の日付でフィルタリング
        if target_date:
            videos_by_date_camera = self.file_parser.filter_by_date(videos_by_date_camera, target_date)
            if not videos_by_date_camera:
                print(f"指定された日付 {target_date} の動画ファイルが見つかりませんでした")
                return
            print(f"対象日付: {target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}")
        else:
            print(f"見つかった日付: {len(videos_by_date_camera)} 日分")
        print()

        # 日付・カメラ別にマージ処理
        success_count = 0
        total_count = 0

        for date_str in sorted(videos_by_date_camera.keys()):
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            print(f"=== 日付: {formatted_date} ===")

            cameras_by_date = videos_by_date_camera[date_str]
            for camera_pos in sorted(cameras_by_date.keys()):
                video_files = cameras_by_date[camera_pos]
                camera_name = self.config.get_camera_name(camera_pos)
                print(f"--- {camera_name}カメラ ({camera_pos}) ---")

                if show_info:
                    self.display_video_info(video_files, camera_name)

                if self.video_merger.merge_videos(video_files, date_str, camera_pos):
                    success_count += 1
                total_count += 1
                print()
            print()

        print(f"マージ完了: {success_count}/{total_count} カメラ分")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='ドライブレコーダーの動画を日付ごとにマージ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s                    # 全ての日付をマージ
  %(prog)s -d 20250906        # 2025年9月6日のみマージ
  %(prog)s -c config/custom.json     # カスタム設定ファイルを使用
  %(prog)s --no-info          # 詳細情報を非表示
        """
    )

    parser.add_argument('-c', '--config',
                       help='設定ファイルのパス（省略時はconfig/config.json）')
    parser.add_argument('--no-info', action='store_true',
                       help='ファイル情報の表示を省略')
    parser.add_argument('-d', '--date',
                       help='特定の日付のみをマージ（YYYYMMDD形式、例：20250906）')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()

    try:
        app = DashcamVideoMergerApp(args.config)
        app.merge_all(show_info=not args.no_info, target_date=args.date)
    except KeyboardInterrupt:
        print("\n処理が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()