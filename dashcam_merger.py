#!/usr/bin/env python3
"""
ドライブレコーダーの細切れ動画を日付ごとに1つの動画にマージするプログラム
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
import subprocess
from collections import defaultdict
import argparse


class DashcamVideoMerger:
    def __init__(self, config_path=None):
        # 設定ファイルを読み込み
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"

        self.config = self.load_config(config_path)
        self.camera_paths = {k: Path(v) for k, v in self.config["camera_paths"].items()}
        self.output_dir = Path(self.config["output_dir"])
        self.camera_names = self.config["camera_names"]
        self.video_pattern = re.compile(self.config["video_pattern"])

        # 出力ディレクトリを作成
        self.output_dir.mkdir(exist_ok=True)

    def load_config(self, config_path):
        """設定ファイルを読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"設定ファイルの形式が正しくありません: {e}")
            sys.exit(1)

    def parse_filename(self, filename):
        """
        ファイル名から日付、時刻、連番、カメラ位置を抽出
        例: NO20250906-134056-000895F.MP4 -> (20250906, 134056, 000895, F)
        """
        match = self.video_pattern.match(filename)
        if match:
            date_str, time_str, sequence, camera_pos = match.groups()
            return date_str, time_str, sequence, camera_pos
        return None, None, None, None

    def get_video_files(self):
        """設定されたカメラパスから動画ファイルを取得し、日付・カメラ位置ごとにグループ化"""
        videos_by_date_camera = defaultdict(lambda: defaultdict(list))

        # 各カメラパスからファイルを取得
        for camera_pos, camera_path in self.camera_paths.items():
            if not camera_path.exists():
                print(f"警告: カメラ {camera_pos} のパスが見つかりません: {camera_path}")
                continue

            for file_path in camera_path.glob("*.MP4"):
                date_str, time_str, sequence, file_camera_pos = self.parse_filename(file_path.name)
                if date_str and file_camera_pos == camera_pos:
                    videos_by_date_camera[date_str][camera_pos].append({
                        'path': file_path,
                        'date': date_str,
                        'time': time_str,
                        'sequence': sequence,
                        'camera_pos': camera_pos,
                        'filename': file_path.name
                    })

        # 各日付・カメラ位置のファイルを時刻順にソート
        for date_str in videos_by_date_camera:
            for camera_pos in videos_by_date_camera[date_str]:
                videos_by_date_camera[date_str][camera_pos].sort(key=lambda x: (x['time'], x['sequence']))

        return videos_by_date_camera

    def create_file_list(self, video_files, date_str, camera_pos):
        """FFmpegで使用するファイルリストを作成"""
        list_file_path = self.output_dir / f"filelist_{date_str}_{camera_pos}.txt"

        with open(list_file_path, 'w', encoding='utf-8') as f:
            for video in video_files:
                # FFmpegのconcatフィルター用のフォーマット
                f.write(f"file '{video['path'].absolute()}'\n")

        return list_file_path

    def merge_videos_for_date_camera(self, date_str, camera_pos, video_files):
        """指定された日付・カメラ位置の動画ファイルをマージ"""
        if not video_files:
            print(f"日付 {date_str} カメラ {camera_pos} の動画ファイルが見つかりませんでした")
            return False

        camera_name = self.camera_names.get(camera_pos, camera_pos)
        print(f"日付 {date_str} {camera_name}カメラ: {len(video_files)} 個のファイルをマージ中...")

        # ファイルリストを作成
        list_file = self.create_file_list(video_files, date_str, camera_pos)

        # 出力ファイル名を生成（日付を読みやすい形式に変換）
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        output_file = self.output_dir / f"merged_{formatted_date}_{camera_pos}.mp4"

        # 設定からFFmpegオプションを取得
        copy_settings = self.config["ffmpeg_settings"]["copy_codec"]
        reencode_settings = self.config["ffmpeg_settings"]["reencode_settings"]

        # 最初にストリームコピーを試行
        cmd_copy = [
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

        # 失敗した場合の再エンコード用コマンド
        cmd_reencode = [
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

        # まずストリームコピーを試行
        try:
            print(f"ストリームコピーでマージを試行中...")
            result = subprocess.run(cmd_copy, capture_output=True, text=True, check=True)
            print(f"マージ完了: {output_file}")
            try:
                list_file.unlink()
            except OSError:
                pass  # 一時ファイルの削除に失敗しても続行
            return True

        except subprocess.CalledProcessError as e:
            print(f"ストリームコピーに失敗。再エンコードを試行中...")

            # 再エンコードを試行
            try:
                result = subprocess.run(cmd_reencode, capture_output=True, text=True, check=True)
                print(f"再エンコードでマージ完了: {output_file}")
                try:
                    list_file.unlink()
                except OSError:
                    pass  # 一時ファイルの削除に失敗しても続行
                return True

            except subprocess.CalledProcessError as e2:
                # ファイルが作成されているかチェック
                if output_file.exists() and output_file.stat().st_size > 0:
                    print(f"警告: エラーが発生しましたが、動画ファイルは作成されました: {output_file}")
                    print(f"ファイルサイズ: {output_file.stat().st_size / (1024*1024):.1f} MB")
                    try:
                        list_file.unlink()
                    except OSError:
                        pass  # 一時ファイルの削除に失敗しても続行
                    return True
                else:
                    print(f"再エンコードも失敗: {e2}")
                    print(f"標準エラー: {e2.stderr}")
                    return False

        except FileNotFoundError:
            print("FFmpegが見つかりません。FFmpegをインストールしてください。")
            return False

    def get_video_info(self, video_files):
        """動画ファイルの情報を表示"""
        if not video_files:
            return

        first_file = video_files[0]
        last_file = video_files[-1]

        print(f"  開始時刻: {first_file['time'][:2]}:{first_file['time'][2:4]}:{first_file['time'][4:6]}")
        print(f"  終了時刻: {last_file['time'][:2]}:{last_file['time'][2:4]}:{last_file['time'][4:6]}")
        print(f"  ファイル数: {len(video_files)}")

        # 総ファイルサイズを計算
        total_size = sum(video['path'].stat().st_size for video in video_files)
        total_size_mb = total_size / (1024 * 1024)
        print(f"  総サイズ: {total_size_mb:.1f} MB")

    def merge_all(self, show_info=True, target_date=None):
        """すべての日付の動画をマージ（target_dateが指定された場合はその日付のみ）"""
        videos_by_date_camera = self.get_video_files()

        if not videos_by_date_camera:
            print("マージ対象の動画ファイルが見つかりませんでした")
            return

        print(f"設定されたカメラパス:")
        for camera_pos, camera_path in self.camera_paths.items():
            camera_name = self.camera_names.get(camera_pos, camera_pos)
            print(f"  {camera_name}カメラ ({camera_pos}): {camera_path}")
        print(f"出力ディレクトリ: {self.output_dir}")

        # 特定の日付が指定された場合はフィルタリング
        if target_date:
            if target_date in videos_by_date_camera:
                videos_by_date_camera = {target_date: videos_by_date_camera[target_date]}
                print(f"対象日付: {target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}")
            else:
                print(f"指定された日付 {target_date} の動画ファイルが見つかりませんでした")
                return
        else:
            print(f"見つかった日付: {len(videos_by_date_camera)} 日分")
        print()

        success_count = 0
        total_count = 0

        for date_str in sorted(videos_by_date_camera.keys()):
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            print(f"=== 日付: {formatted_date} ===")

            cameras_by_date = videos_by_date_camera[date_str]
            for camera_pos in sorted(cameras_by_date.keys()):
                video_files = cameras_by_date[camera_pos]
                camera_name = self.camera_names.get(camera_pos, camera_pos)
                print(f"--- {camera_name}カメラ ({camera_pos}) ---")

                if show_info:
                    self.get_video_info(video_files)

                if self.merge_videos_for_date_camera(date_str, camera_pos, video_files):
                    success_count += 1
                total_count += 1
                print()
            print()

        print(f"マージ完了: {success_count}/{total_count} カメラ分")


def main():
    parser = argparse.ArgumentParser(description='ドライブレコーダーの動画を日付ごとにマージ')
    parser.add_argument('-c', '--config', help='設定ファイルのパス（省略時はconfig.json）')
    parser.add_argument('--no-info', action='store_true', help='ファイル情報の表示を省略')
    parser.add_argument('-d', '--date', help='特定の日付のみをマージ（YYYYMMDD形式、例：20250906）')

    args = parser.parse_args()

    merger = DashcamVideoMerger(args.config)
    merger.merge_all(show_info=not args.no_info, target_date=args.date)


if __name__ == "__main__":
    main()