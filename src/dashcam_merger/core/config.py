"""
設定ファイル管理モジュール
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


class Config:
    """設定ファイルを管理するクラス"""

    def __init__(self, config_path: str = None):
        """
        設定ファイルを読み込む

        Args:
            config_path: 設定ファイルのパス（省略時はconfig/config.json）
        """
        if config_path is None:
            # プロジェクトルートのconfig/config.jsonを参照
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "config" / "config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {self.config_path}")
            print("config/config.json.example をコピーして config/config.json を作成してください")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"設定ファイルの形式が正しくありません: {e}")
            sys.exit(1)

    @property
    def camera_paths(self) -> Dict[str, Path]:
        """カメラごとのパスを取得"""
        return {k: Path(v) for k, v in self.config["camera_paths"].items()}

    @property
    def output_dir(self) -> Path:
        """出力ディレクトリを取得"""
        return Path(self.config["output_dir"])

    @property
    def camera_names(self) -> Dict[str, str]:
        """カメラの表示名を取得"""
        return self.config["camera_names"]

    @property
    def video_pattern(self) -> str:
        """動画ファイルの正規表現パターンを取得"""
        return self.config["video_pattern"]

    @property
    def ffmpeg_copy_settings(self) -> Dict[str, str]:
        """FFmpegのストリームコピー設定を取得"""
        return self.config["ffmpeg_settings"]["copy_codec"]

    @property
    def ffmpeg_reencode_settings(self) -> Dict[str, str]:
        """FFmpegの再エンコード設定を取得"""
        return self.config["ffmpeg_settings"]["reencode_settings"]

    @property
    def use_local_processing(self) -> bool:
        """ローカル処理を使用するかどうかを取得（NAS環境での高速化）"""
        return self.config.get("performance_settings", {}).get("use_local_processing", True)

    def get_camera_name(self, camera_pos: str) -> str:
        """カメラ位置から表示名を取得"""
        return self.camera_names.get(camera_pos, camera_pos)

    def ensure_output_dir(self):
        """出力ディレクトリが存在しない場合は作成"""
        self.output_dir.mkdir(parents=True, exist_ok=True)