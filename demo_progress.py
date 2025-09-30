#!/usr/bin/env python3
"""
プログレス表示機能のデモンストレーション

実際の動画ファイルがなくてもプログレス表示をテストできます
"""

import time
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dashcam_merger.ui.progress import ProgressTracker, SimpleProgressBar


def demo_simple_progress_bar():
    """シンプルプログレスバーのデモ"""
    print("=== シンプルプログレスバーのデモ ===")

    bar = SimpleProgressBar(total=100, description="ファイル処理", width=50)

    for i in range(101):
        bar.update(1, f"ファイル処理 ({i}/100)")
        time.sleep(0.05)  # 処理時間をシミュレート

    bar.close()
    print("シンプルプログレスバー完了\n")


def demo_progress_tracker():
    """プログレストラッカーのデモ"""
    print("=== プログレストラッカーのデモ ===")

    # プログレストラッカーを初期化
    tracker = ProgressTracker(show_progress=True, progress_style="bar")

    # フロントカメラとバックカメラを追加
    tracker.add_camera("F", "フロント", 3, 299.2)
    tracker.add_camera("B", "バック", 2, 95.4)

    # プログレス表示を開始
    tracker.start_display()

    try:
        # フロントカメラの処理をシミュレート
        tracker.update_camera("F", 0, "", 0.0, "フロントカメラ処理開始")
        time.sleep(1)

        tracker.update_camera("F", 1, "NO20250930-140000-000001F.MP4", 100.0, "フロントカメラ ストリームコピー中")
        time.sleep(2)

        tracker.update_camera("F", 2, "NO20250930-140030-000002F.MP4", 200.0, "フロントカメラ ストリームコピー中")
        time.sleep(2)

        tracker.update_camera("F", 3, "merged_2025-09-30_F.mp4", 299.2, "フロントカメラ 完了")

        # バックカメラの処理をシミュレート（並行処理風）
        tracker.update_camera("B", 0, "", 0.0, "バックカメラ処理開始")
        time.sleep(0.5)

        tracker.update_camera("B", 1, "NO20250930-140000-000001B.MP4", 47.0, "バックカメラ 再エンコード中")
        time.sleep(3)

        tracker.update_camera("B", 2, "merged_2025-09-30_B.mp4", 95.4, "バックカメラ 完了")
        time.sleep(1)

    finally:
        # プログレス表示を停止
        tracker.stop_display()
        tracker.print_final_summary()

    print("プログレストラッカーデモ完了\n")


def demo_simple_style():
    """シンプルスタイルのデモ"""
    print("=== シンプルスタイルのデモ ===")

    tracker = ProgressTracker(show_progress=True, progress_style="simple")

    tracker.add_camera("F", "フロント", 2, 200.0)
    tracker.add_camera("B", "バック", 2, 100.0)

    tracker.start_display()

    try:
        for i in range(11):
            progress_f = min(i * 10, 100)
            progress_b = min((i - 2) * 10, 100) if i >= 2 else 0

            tracker.update_camera("F", int(progress_f / 50), f"file_f_{i}.mp4", progress_f * 2,
                                f"フロントカメラ処理中")

            if i >= 2:
                tracker.update_camera("B", int(progress_b / 50), f"file_b_{i-2}.mp4", progress_b,
                                    f"バックカメラ処理中")

            time.sleep(0.5)

    finally:
        tracker.stop_display()
        print("\nシンプルスタイルデモ完了\n")


def main():
    """メイン関数"""
    print("プログレス表示機能デモンストレーション")
    print("=" * 50)

    try:
        demo_simple_progress_bar()
        demo_progress_tracker()
        demo_simple_style()

        print("全てのデモが完了しました！")

    except KeyboardInterrupt:
        print("\n\nデモが中断されました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")


if __name__ == "__main__":
    main()