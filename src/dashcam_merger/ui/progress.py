"""
プログレス表示モジュール

リアルタイムプログレスバーと処理状況表示を提供
"""

import time
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ProgressInfo:
    """プログレス情報を管理するデータクラス"""
    current: int = 0
    total: int = 0
    current_file: str = ""
    current_size_mb: float = 0.0
    total_size_mb: float = 0.0
    start_time: float = field(default_factory=time.time)
    status: str = "待機中"

    @property
    def percentage(self) -> float:
        """進捗率を計算"""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)

    @property
    def elapsed_time(self) -> float:
        """経過時間を計算"""
        return time.time() - self.start_time

    @property
    def estimated_remaining(self) -> float:
        """残り時間を推定"""
        if self.current == 0 or self.percentage == 0:
            return 0.0
        elapsed = self.elapsed_time
        return (elapsed / self.percentage) * (100 - self.percentage)

    @property
    def processing_speed_mb_s(self) -> float:
        """処理速度（MB/s）を計算"""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.current_size_mb / elapsed


class ProgressTracker:
    """プログレス追跡と表示を管理するクラス"""

    def __init__(self, show_progress: bool = True, progress_style: str = "bar"):
        """
        初期化

        Args:
            show_progress: プログレス表示するかどうか
            progress_style: プログレススタイル ("bar", "simple")
        """
        self.show_progress = show_progress
        self.progress_style = progress_style
        self.cameras: Dict[str, ProgressInfo] = {}
        self.overall = ProgressInfo()
        self._display_thread: Optional[threading.Thread] = None
        self._stop_display = threading.Event()
        self._lock = threading.Lock()

    def add_camera(self, camera_pos: str, camera_name: str, total_files: int, total_size_mb: float):
        """カメラの進捗追跡を開始"""
        with self._lock:
            self.cameras[camera_pos] = ProgressInfo(
                total=total_files,
                total_size_mb=total_size_mb,
                status=f"{camera_name}カメラ待機中"
            )
            self._update_overall()

    def update_camera(self, camera_pos: str, current_file: int, current_file_name: str,
                     processed_size_mb: float, status: str):
        """カメラの進捗を更新"""
        with self._lock:
            if camera_pos in self.cameras:
                progress = self.cameras[camera_pos]
                progress.current = current_file
                progress.current_file = current_file_name
                progress.current_size_mb = processed_size_mb
                progress.status = status
                self._update_overall()

    def _update_overall(self):
        """全体の進捗を更新"""
        total_files = sum(cam.total for cam in self.cameras.values())
        current_files = sum(cam.current for cam in self.cameras.values())
        total_size = sum(cam.total_size_mb for cam in self.cameras.values())
        current_size = sum(cam.current_size_mb for cam in self.cameras.values())

        self.overall.total = total_files
        self.overall.current = current_files
        self.overall.total_size_mb = total_size
        self.overall.current_size_mb = current_size
        self.overall.status = f"全体処理中 ({len([c for c in self.cameras.values() if c.current > 0])}/{len(self.cameras)} カメラ)"

    def start_display(self):
        """プログレス表示を開始"""
        if not self.show_progress:
            return

        self._stop_display.clear()
        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()

    def stop_display(self):
        """プログレス表示を停止"""
        if self._display_thread:
            self._stop_display.set()
            self._display_thread.join(timeout=1.0)

    def _display_loop(self):
        """プログレス表示のメインループ"""
        while not self._stop_display.is_set():
            self._render_progress()
            time.sleep(0.5)  # 500ms間隔で更新

    def _render_progress(self):
        """プログレス表示をレンダリング"""
        if self.progress_style == "bar":
            self._render_bar_style()
        else:
            self._render_simple_style()

    def _render_bar_style(self):
        """バースタイルのプログレス表示"""
        with self._lock:
            # 画面をクリア（ANSI escape sequence）
            print("\033[2J\033[H", end="")

            print("=== Dashcam Video Merger - 処理進捗 ===\n")

            # 各カメラの進捗表示
            for camera_pos, progress in self.cameras.items():
                self._render_camera_progress(camera_pos, progress)
                print()

            # 全体進捗表示
            print("=" * 50)
            self._render_overall_progress()
            print()

    def _render_camera_progress(self, camera_pos: str, progress: ProgressInfo):
        """カメラ別プログレス表示"""
        bar_width = 40
        filled_width = int(bar_width * progress.percentage / 100)
        bar = "█" * filled_width + "░" * (bar_width - filled_width)

        print(f"┌─ {progress.status} ─")
        print(f"│ [{bar}] {progress.percentage:5.1f}%")
        print(f"│ ファイル: {progress.current}/{progress.total} | "
              f"サイズ: {progress.current_size_mb:.1f}/{progress.total_size_mb:.1f}MB")

        if progress.current > 0:
            remaining_time = progress.estimated_remaining
            speed = progress.processing_speed_mb_s
            print(f"│ 残り時間: {self._format_time(remaining_time)} | "
                  f"速度: {speed:.1f}MB/s")
            if progress.current_file:
                filename = progress.current_file.split('/')[-1]  # ファイル名のみ
                print(f"│ 処理中: {filename}")

        print("└" + "─" * 48)

    def _render_overall_progress(self):
        """全体プログレス表示"""
        bar_width = 40
        filled_width = int(bar_width * self.overall.percentage / 100)
        bar = "█" * filled_width + "░" * (bar_width - filled_width)

        print(f"全体進捗: [{bar}] {self.overall.percentage:5.1f}%")
        print(f"ファイル: {self.overall.current}/{self.overall.total} | "
              f"サイズ: {self.overall.current_size_mb:.1f}/{self.overall.total_size_mb:.1f}MB")

        if self.overall.current > 0:
            elapsed = self.overall.elapsed_time
            remaining = self.overall.estimated_remaining
            speed = self.overall.processing_speed_mb_s
            print(f"経過時間: {self._format_time(elapsed)} | "
                  f"残り時間: {self._format_time(remaining)} | "
                  f"平均速度: {speed:.1f}MB/s")

    def _render_simple_style(self):
        """シンプルスタイルのプログレス表示"""
        with self._lock:
            status_lines = []
            for camera_pos, progress in self.cameras.items():
                status_lines.append(f"{progress.status}: {progress.percentage:.1f}% "
                                  f"({progress.current}/{progress.total})")

            status_lines.append(f"全体: {self.overall.percentage:.1f}% "
                              f"({self.overall.current}/{self.overall.total})")

            # 一行で表示（前の行を上書き）
            print(f"\r{' | '.join(status_lines)}", end="", flush=True)

    def _format_time(self, seconds: float) -> str:
        """時間を読みやすい形式でフォーマット"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds // 60:.0f}m{seconds % 60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h{minutes:.0f}m"

    def print_final_summary(self):
        """最終結果サマリーを表示"""
        if not self.show_progress:
            return

        print("\n" + "=" * 50)
        print("処理完了サマリー")
        print("=" * 50)

        for camera_pos, progress in self.cameras.items():
            elapsed = progress.elapsed_time
            avg_speed = progress.processing_speed_mb_s
            print(f"{progress.status}: {progress.total}ファイル "
                  f"({progress.total_size_mb:.1f}MB) "
                  f"処理時間: {self._format_time(elapsed)} "
                  f"平均速度: {avg_speed:.1f}MB/s")

        total_elapsed = self.overall.elapsed_time
        total_speed = self.overall.processing_speed_mb_s
        print(f"\n全体: {self.overall.total}ファイル "
              f"({self.overall.total_size_mb:.1f}MB) "
              f"処理時間: {self._format_time(total_elapsed)} "
              f"平均速度: {total_speed:.1f}MB/s")
        print("=" * 50)


class SimpleProgressBar:
    """軽量なプログレスバー（外部依存なし版）"""

    def __init__(self, total: int, description: str = "", width: int = 40):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()

    def update(self, amount: int = 1, description: str = None):
        """プログレスを更新"""
        self.current = min(self.current + amount, self.total)
        if description:
            self.description = description
        self._display()

    def _display(self):
        """プログレスバーを表示"""
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        filled_width = int(self.width * self.current / self.total) if self.total > 0 else 0
        bar = "█" * filled_width + "░" * (self.width - filled_width)

        elapsed = time.time() - self.start_time
        if self.current > 0 and elapsed > 0:
            speed = self.current / elapsed
            remaining = (self.total - self.current) / speed if speed > 0 else 0
            time_info = f" | {self._format_time(remaining)} 残り"
        else:
            time_info = ""

        print(f"\r{self.description}: [{bar}] {percentage:5.1f}% "
              f"({self.current}/{self.total}){time_info}", end="", flush=True)

    def _format_time(self, seconds: float) -> str:
        """時間フォーマット"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds // 60:.0f}m{seconds % 60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h{minutes:.0f}m"

    def close(self):
        """プログレスバーを終了"""
        print()  # 改行