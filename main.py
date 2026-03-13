import argparse
import os
import subprocess
from datetime import datetime

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.theme import Theme
    _console = Console(theme=Theme({
        "markdown.h1": "bold white",
        "markdown.h2": "bold cyan",
        "markdown.h3": "bold blue",
        "markdown.code": "bright_black on grey23",
        "markdown.code_block": "bright_black on grey23",
        "markdown.link": "cyan underline",
    }))
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
            Markdown(content),
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
