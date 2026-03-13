# note

ターミナルで完結するナレッジ管理 CLI。Markdownノートの作成・編集・検索・GitHub同期をワンコマンドで行う。

---

## 必要なもの

| ツール | 用途 | 必須 |
|--------|------|------|
| Python 3.12+ | 実行環境 | ✅ |
| nvim | ノート編集 | ✅ |
| rich | ターミナルMarkdownレンダリング | ✅ |
| rg (ripgrep) | 高速全文検索 | 任意（なければ grep で代用） |

```bash
pip install rich
brew install ripgrep   # 任意
```

---

## セットアップ

```bash
# リポジトリをクローン
git clone git@github.com:bellsmarket/note.git
cd note

# 依存パッケージインストール
pip install rich

# ノートリポジトリを GitHub から取得（初回のみ）
python3 main.py -p

# シンボリックリンクを作成（任意）
ln -s "$(pwd)/note" ~/bin/note
```

### zsh 補完の有効化

```bash
mkdir -p ~/.zsh/completion
cp _note ~/.zsh/completion/_note
```

`~/.zshrc` に以下が含まれていることを確認:

```zsh
fpath=(~/.zsh/completion $fpath)
autoload -Uz compinit && compinit
```

---

## 使い方

```
note [OPTIONS]
```

### コマンド一覧

| コマンド | 説明 |
|----------|------|
| `note <name>` | ノートを作成（既存なら編集へ） |
| `note -c <name>` | 新規ノートを作成して nvim で開く |
| `note -e <name>` | 既存ノートを nvim で編集（なければ作成提案） |
| `note -r <name>` | ノートを rich でレンダリング表示 |
| `note -l` | ノート一覧を表示 |
| `note -s <query>` | 全ノートをキーワード検索（rg / grep） |
| `note -p` | GitHub からノートを pull（未clone なら clone） |
| `note --push` | 変更を GitHub へ push（デフォルトメッセージ: "update"） |
| `note --push "msg"` | コミットメッセージを指定して push |
| `note --open <editor>` | ノートディレクトリを GUI エディタで開く |

### `--open` で使えるエディタ

| キー | アプリ |
|------|--------|
| `obsidian` | Obsidian |
| `typora` | Typora |
| `pulsar` | Pulsar（旧 Atom） |
| `boostnote` | Boostnote |

---

## 使用例

```bash
# 新規作成（.md は省略可）
note -c docker

# 既存ノートを編集
note -e docker

# ターミナルでレンダリング表示
note -r docker

# ノート一覧
note -l

# キーワード検索
note -s "WIP"
note -s "Reminder"

# GitHub 同期
note -p
note --push
note --push "add docker notes"

# GUI エディタで開く
note --open obsidian
```

---

## ノートのテンプレート

新規作成時に以下のテンプレートが自動挿入される:

```markdown
---
description:
created: 2025-01-01 12:00:00
---

# myfile

## Table of Contents
- Description
- Header 01
- Header 02
```

`description:` フィールドに説明を書くと、タブ補完時に表示される。

---

## タブ補完

`note -e <Tab>` でノート名を補完。`description:` frontmatter があれば説明も表示される。

```
note -e
  docker      -- Dockerの基本コマンドまとめ
  git         -- Gitワークフローメモ
  shell       -- シェルスクリプト逆引き
```

ファイル名は `.md` あり・なしどちらで入力しても正しく動作する。

---

## Markdown レンダリング チートシート

`note -r <name>` で表示したときの各要素の見え方。`glow` 等の外部ツール不要。

### 見出し

```markdown
# H1
## H2
### H3
```

```
⏺ H1                        ← bold cyan
  ⏺ H2                      ← bold green
    ⏺ H3                    ← bold blue
```

### テキスト装飾

```markdown
**太字**  *斜体*  ~~取り消し~~  `インラインコード`
```

```
太字  斜体  ~~取り消し~~  インラインコード（グレー背景）
```

### コードブロック

````markdown
```bash
echo "hello"
```
````

```
 echo "hello"       ← グレー背景・シンタックスハイライト
```

### リスト

```markdown
- item A
- item B
  - nested
```

```
 • item A
 • item B
     • nested
```

### 番号付きリスト

```markdown
1. first
2. second
```

```
 1 first
 2 second
```

### テーブル

```markdown
| Col A | Col B |
|-------|-------|
| foo   | bar   |
```

```
 Col A  Col B
 ─────────────
 foo    bar
```

### リンク

```markdown
[テキスト](https://example.com)
```

```
テキスト                        ← cyan + underline
```

### 引用

```markdown
> 引用テキスト
```

```
│ 引用テキスト                  ← 左にバー
```

### 水平線

```markdown
---
```

```
────────────────────────────────
```

### Frontmatter

ファイル先頭の `---` ブロックは表示時にそのまま描画される（非表示にはならない）。
ノート作成時のテンプレートに含まれる `description:` と `created:` フィールドが対象。

---

`rich` がインストールされていない場合はプレーンテキストで出力。

---

## 検索 TIPS

```bash
# WIP（作業中）ノートを探す
note -s "WIP"

# リマインダーを探す
note -s "Reminder"

# 正規表現（rg のみ）
note -s "docker|kubernetes"
```

---

## ビルド（PyInstaller）

```bash
pip install pyinstaller rich
pyinstaller main.spec

# バイナリは dist/main に生成される
cp dist/main /usr/local/bin/note
```

---

## ノートの保存先

```
~/ghq/github.com/bellsmarket/.note/
```

`main.py` の `NOTE_DIR` を変更すれば任意のディレクトリに移動できる。

---

## 既知の改善点・TODO

- [ ] ノート削除コマンド（`-d`）の追加
- [ ] `note -l` にファイルサイズ・更新日時の表示
- [ ] fzf 連携（ファジー検索で選択 → 即編集）
- [ ] ノートのタグ管理（frontmatter ベース）
- [ ] `note -r` でページャー対応（長いノートのスクロール）
- [ ] テンプレートの種類を選べるオプション（`--template`）
