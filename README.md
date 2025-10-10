# Dashcam Video Merger

ドライブレコーダーの細切れ動画を日付・カメラ別にマージするPythonプログラム

## 機能

- **日付別自動グループ化**: ファイル名から日付を自動抽出し、同じ日付の動画をマージ
- **マルチカメラ対応**: フロント（F）・バック（B）カメラを個別に処理
- **設定ファイル管理**: JSONで複数カメラのパス設定を一元管理
- **フォールバック処理**: ストリームコピー失敗時は自動で再エンコード
- **時系列ソート**: 時刻と連番で正確な順序でマージ
- **NAS環境最適化**: ローカル一時処理によりネットワークストレージでの高速化

## 対応ファイル形式

ドライブレコーダーのファイル名規則: `NO20250906-134056-000895F.MP4`
- 日付: 20250906 (YYYYMMDD)
- 時刻: 134056 (HHMMSS)
- 連番: 000895
- カメラ: F（フロント）/ B（バック）

## 必要要件

- Python 3.6+
- FFmpeg

### FFmpegのインストール

```bash
# macOS (Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

## プロジェクト構造

```
dashcam-video-merger/
├── src/
│   └── dashcam_merger/           # メインパッケージ
│       ├── __init__.py
│       ├── __main__.py          # python -m dashcam_merger エントリーポイント
│       ├── core/                # コア機能（設定・データモデル）
│       │   ├── config.py
│       │   └── models.py
│       ├── parsers/             # ファイル解析
│       │   └── file_parser.py
│       ├── processors/          # 動画処理
│       │   └── video_merger.py
│       └── cli/                 # コマンドラインインターフェース
│           └── main.py
├── scripts/
│   └── dashcam_merger.py        # 実行スクリプト（後方互換性）
├── config/
│   ├── config.json             # 設定ファイル
│   └── config.json.example     # 設定ファイルサンプル
├── docs/
│   └── ARCHITECTURE.md         # アーキテクチャ設計書
├── tests/                      # テストファイル（今後追加予定）
├── pyproject.toml              # モダンなPython設定
├── requirements.txt
└── README.md                   # このファイル
```

## セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/H1R0Kazu/dashcam-video-merger.git
cd dashcam-video-merger
```

2. 設定ファイルを作成・編集
```bash
cp config/config.json.example config/config.json
# config/config.jsonを環境に合わせて編集
```

## 設定ファイル例

```json
{
  "camera_paths": {
    "F": "/path/to/front/camera/videos",
    "B": "/path/to/back/camera/videos"
  },
  "output_dir": "/path/to/output/directory",
  "camera_names": {
    "F": "フロント",
    "B": "バック"
  },
  "video_pattern": "NO(\\\\d{8})-(\\\\d{6})-(\\\\d{6})([FB])\\\\.MP4",
  "ffmpeg_settings": {
    "copy_codec": {
      "video": "copy",
      "audio": "copy"
    },
    "reencode_settings": {
      "video_codec": "libx264",
      "audio_codec": "aac",
      "preset": "fast",
      "crf": "23"
    }
  },
  "performance_settings": {
    "use_local_processing": true,
    "comment": "NAS環境での高速化: ローカル一時ディレクトリを使用してマージ処理を高速化"
  }
}
```

## 使用方法

### 基本的な使用方法

```bash
# 推奨方法：モジュールとして実行
PYTHONPATH=src python3 -m dashcam_merger

# 特定の日付のみマージ
PYTHONPATH=src python3 -m dashcam_merger -d 20250906

# カスタム設定ファイルを使用
PYTHONPATH=src python3 -m dashcam_merger -c config/custom.json

# 詳細情報を非表示
PYTHONPATH=src python3 -m dashcam_merger --no-info

# 簡単な実行方法（スクリプト経由）
python3 scripts/dashcam_merger.py -d 20250906
```

### オプション

- `-c, --config`: 設定ファイルのパス（デフォルト: config/config.json）
- `-d, --date`: 特定日付のみ処理（YYYYMMDD形式）
- `--no-info`: ファイル情報表示を省略

## 出力

マージされた動画は以下の形式で保存されます：
- フロントカメラ: `merged_2025-09-06_F.mp4`
- バックカメラ: `merged_2025-09-06_B.mp4`

## 動作例

```
設定されたカメラパス:
  フロントカメラ (F): /path/to/front/videos
  バックカメラ (B): /path/to/back/videos
出力ディレクトリ: /path/to/output

=== 日付: 2025-09-06 ===
--- バックカメラ (B) ---
  開始時刻: 13:40:56
  終了時刻: 13:41:56
  ファイル数: 2
  総サイズ: 95.4 MB
日付 20250906 バックカメラ: 2 個のファイルをマージ中...
ストリームコピーでマージを試行中...
マージ完了: /path/to/output/merged_2025-09-06_B.mp4

--- フロントカメラ (F) ---
  開始時刻: 13:40:56
  終了時刻: 13:41:56
  ファイル数: 2
  総サイズ: 299.2 MB
日付 20250906 フロントカメラ: 2 個のファイルをマージ中...
ストリームコピーでマージを試行中...
マージ完了: /path/to/output/merged_2025-09-06_F.mp4

マージ完了: 2/2 カメラ分
```

## トラブルシューティング

### FFmpegが見つからない
```
FFmpegが見つかりません。FFmpegをインストールしてください。
```
→ FFmpegをインストールしてパスを通してください。

### パケット破損エラー
一部の動画ファイルでストリームコピーが失敗する場合がありますが、プログラムは自動的に再エンコードにフォールバックします。

### ディスクスペース不足
マージ前にディスクの空き容量を確認してください。再エンコードの場合、元ファイルより大きくなる場合があります。

### NAS環境での処理が遅い場合
NAS（ネットワークストレージ）環境では処理が遅くなることがあります。以下の最適化オプションが利用できます：

- **ローカル処理モード（推奨）**: `"use_local_processing": true`（デフォルト）
- **従来の直接処理**: `"use_local_processing": false`

ローカル処理モードでは、一時ファイルをローカルディスクで処理してから最終結果をNASに移動するため、大幅な高速化が期待できます。

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 更新履歴

- v1.2.0-dev: 開発環境改善
  - `.gitignore`にmacOSファイルと機密情報ファイル追加
  - セキュリティ向上（MCPトークン保護）
- v1.1.0: NAS環境最適化対応
  - ローカル一時処理による高速化
  - FFmpegネットワーク読み込み最適化
  - 設定による処理モード切り替え
- v1.0.0: 初回リリース
  - 日付別動画マージ機能
  - マルチカメラ対応
  - 設定ファイル対応
  - フォールバック再エンコード機能