# Dashcam Video Merger

ドライブレコーダーの細切れ動画を日付・カメラ別にマージするPythonプログラム

## 機能

- **日付別自動グループ化**: ファイル名から日付を自動抽出し、同じ日付の動画をマージ
- **マルチカメラ対応**: フロント（F）・バック（B）カメラを個別に処理
- **設定ファイル管理**: JSONで複数カメラのパス設定を一元管理
- **フォールバック処理**: ストリームコピー失敗時は自動で再エンコード
- **時系列ソート**: 時刻と連番で正確な順序でマージ

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

## セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/H1R0Kazu/dashcam-video-merger.git
cd dashcam-video-merger
```

2. 設定ファイルを編集
```bash
cp config.json.example config.json
# config.jsonを環境に合わせて編集
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
  }
}
```

## 使用方法

### 基本的な使用方法

```bash
# 全ての日付をマージ
python3 dashcam_merger.py

# 特定の日付のみマージ
python3 dashcam_merger.py -d 20250906

# カスタム設定ファイルを使用
python3 dashcam_merger.py -c custom_config.json

# 詳細情報を非表示
python3 dashcam_merger.py --no-info
```

### オプション

- `-c, --config`: 設定ファイルのパス（デフォルト: config.json）
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

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 更新履歴

- v1.0.0: 初回リリース
  - 日付別動画マージ機能
  - マルチカメラ対応
  - 設定ファイル対応
  - フォールバック再エンコード機能