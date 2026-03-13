import argparse
import os
import subprocess
from datetime import datetime

try:
    import re
    from rich import box as rich_box
    from rich.console import Console, Group
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table as RichTable
    from rich.text import Text
    from rich.theme import Theme

    _console = Console(theme=Theme({
        "markdown.code": "bright_black on grey23",
        "markdown.code_block": "bright_black on grey23",
        "markdown.link": "cyan underline",
    }))

    _HEADING_STYLES = {
        1: ("⏺", "bold cyan"),
        2: ("  ⏺", "bold green"),
        3: ("    ⏺", "bold blue"),
    }

    _TABLE_SEP = re.compile(r'^\|[\s\|\-:]+\|?\s*$')

    def _parse_md_table(lines):
        """Markdown テーブル行を rich Table (SQUARE box) に変換"""
        def split_row(line):
            return [c.strip() for c in line.strip().strip('|').split('|')]

        sep_idx = next((i for i, l in enumerate(lines) if _TABLE_SEP.match(l)), 1)
        headers = split_row(lines[0])
        data_rows = [split_row(l) for l in lines[sep_idx + 1:] if l.strip()]

        t = RichTable(box=rich_box.SQUARE, show_lines=True, header_style="bold")
        for h in headers:
            t.add_column(h)
        for row in data_rows:
            padded = row + [''] * max(0, len(headers) - len(row))
            t.add_row(*padded[:len(headers)])
        return t

    def _render_claude_style(content: str):
        """見出し・テーブルを Claude スタイルで描画、それ以外は Markdown に委譲"""
        parts = []
        buf = []
        table_buf = []
        in_code = False

        def flush_buf():
            if buf:
                parts.append(Markdown('\n'.join(buf)))
                buf.clear()

        def flush_table():
            if table_buf:
                parts.append(_parse_md_table(table_buf))
                table_buf.clear()

        for line in content.split('\n'):
            if line.startswith('```'):
                in_code = not in_code

            if not in_code:
                if line.startswith('|'):
                    flush_buf()
                    table_buf.append(line)
                    continue
                else:
                    flush_table()

                m = re.match(r'^(#{1,3})\s+(.+)', line)
                if m:
                    flush_buf()
                    level = len(m.group(1))
                    symbol, style = _HEADING_STYLES.get(level, ("⏺", "bold white"))
                    t = Text()
                    t.append(f"{symbol} ", style=style)
                    t.append(m.group(2), style=style)
                    parts.append(t)
                    continue

            buf.append(line)

        flush_table()
        flush_buf()
        return Group(*parts)

    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

NOTE_DIR = os.path.expanduser('~/ghq/github.com/bellsmarket/.note')
GIT_REPO = 'git@github.com:bellsmarket/.note.git'

# ripgrep が使えるか起動時に確認、なければ grep で代用
_HAS_RG = subprocess.run(['which', 'rg'], capture_output=True).returncode == 0


def _note_path(file_name):
    """拡張子がなければ .md を付与してフルパスを返す"""
    if not file_name.endswith('.md'):
        file_name += '.md'
    return os.path.join(NOTE_DIR, file_name)


def create_note(file_name):
    file_path = _note_path(file_name)
    base = os.path.splitext(os.path.basename(file_path))[0]
    if os.path.exists(file_path):
        print(f"{base}.md already exists.")
        response = input(f"Open [{base}] for editing? [y/n]: ")
        if response.lower() in ['y', 'yes']:
            subprocess.run(['nvim', file_path])
    else:
        with open(file_path, 'w') as f:
            f.write(f"---\ndescription: \ncreated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n---\n\n")
            f.write(f"# {base}\n\n")
            f.write("## Table of Contents\n- Description\n- Header 01\n- Header 02\n\n")
        print(f"Created: {base}.md")
        subprocess.run(['nvim', file_path])


def read_note(file_name):
    file_path = _note_path(file_name)
    if not os.path.exists(file_path):
        print(f"Not found: {file_path}")
        return
    if _HAS_RICH:
        with open(file_path) as f:
            content = f.read()
        base = os.path.splitext(os.path.basename(file_path))[0]
        _console.print()
        _console.print(Panel(
            _render_claude_style(content),
            title=f"[bold cyan]{base}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ))
        _console.print()
    else:
        with open(file_path) as f:
            print(f.read())


def edit_note(file_name):
    file_path = _note_path(file_name)
    if os.path.exists(file_path):
        subprocess.run(['nvim', file_path])
    else:
        print(f"Not found: {file_path}")
        response = input(f"Create [{file_name}]? [y/n]: ")
        if response.lower() in ['y', 'yes']:
            create_note(file_name)


def get_list():
    if not os.path.isdir(NOTE_DIR):
        print(f"Note directory not found: {NOTE_DIR}")
        return
    files = sorted(f for f in os.listdir(NOTE_DIR) if f.endswith('.md'))
    if not files:
        print("No notes found.")
        return
    print(f"Notes in {NOTE_DIR}:\n")
    for i, f in enumerate(files, 1):
        print(f"  {i:3}. {f}")
    print(f"\nTotal: {len(files)}")


def search_notes(query):
    if not os.path.isdir(NOTE_DIR):
        print(f"Note directory not found: {NOTE_DIR}")
        return
    if _HAS_RG:
        cmd = ['rg', '--color=always', '-i', query, NOTE_DIR]
    else:
        cmd = ['grep', '-r', '-i', '--color=always', query, NOTE_DIR]
    result = subprocess.run(cmd)
    if result.returncode == 1:
        print(f"No matches for: {query}")


def pull_note_from_github():
    if os.path.isdir(os.path.join(NOTE_DIR, '.git')):
        print("Pulling latest changes...")
        subprocess.run(['git', '-C', NOTE_DIR, 'pull'], check=True)
    else:
        os.makedirs(NOTE_DIR, exist_ok=True)
        print("Cloning repository...")
        subprocess.run(['git', 'clone', GIT_REPO, NOTE_DIR], check=True)
    print("Done.")


def push_to_github(message='update'):
    if not os.path.isdir(NOTE_DIR):
        print(f"Directory not found: {NOTE_DIR}")
        return
    try:
        subprocess.run(['git', '-C', NOTE_DIR, 'add', '*.md'], check=True)
        subprocess.run(['git', '-C', NOTE_DIR, 'commit', '-m', message], check=True)
        subprocess.run(['git', '-C', NOTE_DIR, 'push'], check=True)
        print("Pushed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")


def open_editor(editor):
    editors = {
        'pulsar': ['pulsar', NOTE_DIR],
        'obsidian': ['open', '-a', 'Obsidian', NOTE_DIR],
        'typora': ['open', '-a', 'Typora', NOTE_DIR],
        'boostnote': ['open', '-a', 'Boostnote', NOTE_DIR],
    }
    cmd = editors.get(editor.lower())
    if cmd:
        subprocess.run(cmd)
    else:
        print(f"Unknown editor: {editor}. Choose from: {', '.join(editors)}")


def main():
    parser = argparse.ArgumentParser(
        description='Note management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  note -c myfile          # Create new note
  note -e myfile          # Edit existing note
  note -r myfile          # Read note (glow)
  note -l                 # List all notes
  note -s "search term"   # Search notes with ripgrep
  note -p                 # Pull from GitHub
  note --push             # Push to GitHub
  note --open obsidian    # Open in editor
"""
    )
    parser.add_argument('filename', nargs='?', help='Note filename (without .md)')
    parser.add_argument('-c', '--create', metavar='NAME', help='Create new note')
    parser.add_argument('-e', '--edit', metavar='NAME', help='Edit note')
    parser.add_argument('-r', '--read', metavar='NAME', help='Read note (glow)')
    parser.add_argument('-l', '--list', action='store_true', help='List all notes')
    parser.add_argument('-s', '--search', metavar='QUERY', help='Search notes with ripgrep')
    parser.add_argument('-p', '--pull', action='store_true', help='Pull from GitHub')
    parser.add_argument('--push', metavar='MSG', nargs='?', const='update', help='Push to GitHub with optional commit message')
    parser.add_argument('--open', metavar='EDITOR', help='Open note dir in editor (pulsar/obsidian/typora/boostnote)')
    args = parser.parse_args()

    if args.pull:
        pull_note_from_github()
    elif args.push is not None:
        push_to_github(args.push)
    elif args.create:
        create_note(args.create)
    elif args.edit:
        edit_note(args.edit)
    elif args.read:
        read_note(args.read)
    elif args.list:
        get_list()
    elif args.search:
        search_notes(args.search)
    elif args.open:
        open_editor(args.open)
    elif args.filename:
        # 引数だけ渡された場合は作成 or 編集
        create_note(args.filename)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
