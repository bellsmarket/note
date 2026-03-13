# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

```
note        ← bash wrapper (4 lines) — entry point via ~/bin/note symlink
main.py     ← all logic lives here (Python 3)
main.spec   ← PyInstaller build config (optional standalone binary)
~/.zsh/completion/_note → /Users/Shared/dotfiles/zsh/completion/_note  (zsh tab completion)
```

`~/bin/note` is a symlink to `note`. The bash script resolves the symlink with `readlink` and calls `python3 main.py "$@"`. **All changes should be made in `main.py`.**

## Key constants (main.py)

```python
NOTE_DIR = ~/ghq/github.com/bellsmarket/.note   # where .md files live
GIT_REPO = git@github.com:bellsmarket/.note.git
```

## Rendering pipeline

`read_note()` calls `_render_claude_style(content)` which:
1. Detects headings (`#`/`##`/`###`) → renders as `⏺ text` with bold cyan/green/blue via `rich.text.Text`
2. Detects markdown table blocks (lines starting with `|`) → renders with `rich.table.Table(box=SQUARE, show_lines=True)`
3. Everything else → passed to `rich.markdown.Markdown`
4. All parts combined with `rich.console.Group` and wrapped in `rich.panel.Panel`

`rich` import is wrapped in `try/except` — falls back to plain `print()` if not installed. `rg` availability is checked at startup via `which rg`; falls back to `grep -r -i`.

## Development

Changes to `main.py` take effect immediately (no build step). Test with:
```bash
python3 main.py --help
python3 main.py -l
python3 main.py -r <notename>
```

After editing the zsh completion file (`/Users/Shared/dotfiles/zsh/completion/_note`):
```bash
rm -f ~/.zcompdump && exec zsh
```

## PyInstaller build (optional)

Only needed for a standalone binary that doesn't require Python:
```bash
pip install pyinstaller rich
pyinstaller main.spec   # output: dist/main
```

`main.spec` includes `hiddenimports` for `rich` so it bundles correctly.

## Zsh completion

Completion file uses `_describe 'note files' entries` with a **single array** of `"name:description"` strings (not two separate arrays — that caused scope issues with `_describe`). Descriptions come from the `description:` frontmatter field of each `.md` file, parsed with `awk`.

## Background / History

- Originally (v1.x) this was a pure bash script (`note`) with all logic inline — `getopts`, `nvim`, `glow`, `rg`, etc.
- `glow` was used for markdown display but caused external dependency issues → replaced with `rich`
- `main.py` was added alongside the bash script; initially only `read_note` called Python for display
- v2.0.0 (2026-03-14): bash script replaced with a thin wrapper; all logic migrated to `main.py`
- The bash script had a bug where `pull_note_from_github` was called on **every invocation** — intentionally not replicated in Python
- `_variable_color.sh` (from dotfiles) was sourced for color output in bash — no longer needed
- Zsh completion went through several iterations: two-array `_describe` caused `desc=''` spam on every tab press → fixed by using single-array `"name:description"` format
- Table rendering was added after headings: detects `|`-prefixed lines and renders with `rich.table.Table(box=SQUARE)`

## Note template (frontmatter)

All new notes created with `-c` include:
```yaml
---
description:
created: YYYY-MM-DD HH:MM:SS
---
```
The `description:` value appears in zsh tab completion.
