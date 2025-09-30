# MCP Server Setup Guide

## GitHubのMCPサーバー設定

このガイドでは、ダッシュカム動画マージプロジェクトでMCP（Model Context Protocol）サーバーを設定し、Claude CodeからGitHubリポジトリにアクセスできるようにします。

## 前提条件

- Node.js がインストールされていること
- GitHubアカウントとPersonal Access Token
- Claude Code または他のMCP対応AIツール

## 設定手順

### 1. GitHub Personal Access Token の作成

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)" をクリック
3. 以下の権限を付与：
   ```
   - repo (Full control of private repositories)
   - read:org (Read org and team membership)
   - read:user (Read user profile data)
   - user:email (Access user email addresses)
   ```

### 2. Claude Code設定ファイルの更新

すでに設定済みのファイル：`~/.claude/plugins/config.json`

```json
{
  "repositories": {},
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_TOKEN_HERE"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/miyatahirokazu/Documents/GitHub"],
      "env": {}
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "/Users/miyatahirokazu/Documents/GitHub/learn_claude_code2/dashcam_video_merger"],
      "env": {}
    }
  }
}
```

### 3. トークンの設定

1. 上記のJSONファイルを編集
2. `YOUR_TOKEN_HERE` を実際のGitHub Personal Access Tokenに置き換え

### 4. 利用可能なMCPサーバー

#### GitHub Server
- **機能**: リポジトリ管理、Issue作成、PR管理、コード検索
- **用途**: GitHubの操作を自然言語で実行

#### Filesystem Server
- **機能**: ローカルファイルシステムアクセス
- **用途**: プロジェクトファイルの読み書き

#### Git Server
- **機能**: Gitリポジトリ操作
- **用途**: コミット、ブランチ、マージ操作

## 使用例

設定完了後、Claude Codeで以下のような操作が可能になります：

```
「GitHubリポジトリの最新のIssueを確認して」
「新しいブランチを作成してプルリクエストを送って」
「コードの変更を自動でコミットして」
```

## トラブルシューティング

### MCPサーバーが認識されない場合
1. Claude Codeを再起動
2. Node.jsとnpmが最新版か確認
3. ネットワーク接続を確認

### 認証エラーの場合
1. Personal Access Tokenの権限を確認
2. トークンの有効期限を確認
3. 設定ファイルの JSON形式が正しいか確認

### パフォーマンス問題
- リモートMCPサーバー（`github-remote`）の利用も検討
- ローカルバイナリ版の利用で高速化可能

## 代替設定（最新公式サーバー）

`~/.claude/mcp_servers_official.json` に最新の公式サーバー設定も用意済み：

```json
{
  "mcpServers": {
    "github-remote": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

## セキュリティ注意事項

- Personal Access Tokenは機密情報として扱う
- 最小権限の原則に従ってトークン権限を設定
- 定期的にトークンをローテーション
- 設定ファイルをバージョン管理に含めない

---

**更新日**: 2025年9月30日
**対応バージョン**: Claude Code latest, MCP Protocol 2025.4.x