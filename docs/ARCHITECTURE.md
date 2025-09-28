# アーキテクチャ設計書

## 概要

ドライブレコーダー動画マージシステムは、機能別にモジュール化された構造を採用しています。

## ファイル構造

```
dashcam_video_merger/
├── __init__.py              # パッケージ初期化
├── main.py                  # メインエントリーポイント
├── dashcam_merger.py        # main.pyへのシンボリックリンク（後方互換性）
├── config.py                # 設定管理モジュール
├── file_parser.py           # ファイル解析・検索モジュール
├── video_merger.py          # 動画マージ処理モジュール
├── config.json.example      # 設定ファイルサンプル
├── config.json              # 実際の設定ファイル（.gitignoreで除外）
├── dashcam_merger_old.py    # 旧モノリシック版（参考）
└── README.md               # 使用方法ドキュメント
```

## モジュール設計

### 1. config.py - 設定管理モジュール

**責務**: 設定ファイルの読み込み・検証・アクセス

**主要クラス**:
- `Config`: 設定ファイル管理

**主要機能**:
- JSON設定ファイルの読み込み
- 設定値のプロパティアクセス
- 出力ディレクトリの自動作成
- エラーハンドリング

```python
config = Config("config.json")
camera_paths = config.camera_paths
output_dir = config.output_dir
```

### 2. file_parser.py - ファイル解析・検索モジュール

**責務**: 動画ファイルの検索・解析・グループ化

**主要クラス**:
- `VideoFile`: 動画ファイル情報のデータクラス
- `VideoFileParser`: ファイル解析・検索処理

**主要機能**:
- ファイル名の正規表現解析
- カメラパスからのファイル検索
- 日付・カメラ別グループ化
- 時系列ソート
- ファイル情報の取得

```python
parser = VideoFileParser(config)
videos = parser.find_video_files()
info = parser.get_video_info(video_files)
```

### 3. video_merger.py - 動画マージ処理モジュール

**責務**: FFmpegを使用した動画マージ処理

**主要クラス**:
- `VideoMerger`: 動画マージ処理

**主要機能**:
- FFmpeg用ファイルリスト作成
- ストリームコピーでのマージ
- 失敗時の再エンコードフォールバック
- 一時ファイルの管理
- エラーハンドリング

```python
merger = VideoMerger(config)
success = merger.merge_videos(video_files, date_str, camera_pos)
```

### 4. main.py - メインアプリケーション

**責務**: ユーザーインターフェース・全体制御

**主要クラス**:
- `DashcamVideoMergerApp`: アプリケーション制御

**主要機能**:
- コマンドライン引数の解析
- 各モジュールの統合
- 進捗表示・ログ出力
- エラーハンドリング

## データフロー

```
1. main.py
   ↓ (コマンドライン引数解析)
2. Config
   ↓ (設定読み込み)
3. VideoFileParser
   ↓ (ファイル検索・グループ化)
4. VideoMerger
   ↓ (FFmpegでマージ)
5. 出力ファイル生成
```

## 設計原則

### 単一責任原則 (SRP)
各モジュールは1つの責務のみを持つ：
- `config.py`: 設定管理のみ
- `file_parser.py`: ファイル処理のみ
- `video_merger.py`: マージ処理のみ

### 依存関係逆転原則 (DIP)
- `VideoFileParser`と`VideoMerger`は`Config`に依存
- `main.py`がすべてのモジュールを統合
- 循環依存の排除

### オープンクローズド原則 (OCP)
- 新しいカメラタイプの追加が容易
- FFmpeg設定の拡張が可能
- ファイル名パターンの変更に対応

## 拡張ポイント

### 1. 新しいファイル形式対応
`file_parser.py`の`video_pattern`プロパティを変更

### 2. 新しいエンコーダー対応
`config.json`の`ffmpeg_settings`に新しい設定を追加

### 3. 新しいカメラタイプ
`config.json`の`camera_paths`と`camera_names`に追加

### 4. UI拡張
`main.py`の`DashcamVideoMergerApp`クラスを拡張

## テスト戦略

### 単体テスト
各モジュールを個別にテスト：
```python
# config_test.py
def test_config_loading():
    config = Config("test_config.json")
    assert config.output_dir.exists()

# file_parser_test.py
def test_filename_parsing():
    parser = VideoFileParser(config)
    result = parser.parse_filename("NO20250906-134056-000895F.MP4")
    assert result == ("20250906", "134056", "000895", "F")
```

### 統合テスト
モジュール間の連携をテスト：
```python
def test_full_workflow():
    app = DashcamVideoMergerApp("test_config.json")
    app.merge_all(target_date="20250906")
    # 出力ファイルの存在確認
```

## パフォーマンス考慮

1. **ファイル検索の最適化**: glob パターンマッチングの効率化
2. **メモリ使用量**: 大量ファイル処理時のメモリ管理
3. **並列処理**: 将来的に複数カメラの同時処理対応

## セキュリティ考慮

1. **パストラバーサル対策**: ファイルパスの検証
2. **設定ファイル保護**: 機密情報の.gitignore除外
3. **入力検証**: ファイル名・日付形式の厳密チェック