# LaTeX Editor

A local, Overleaf-style LaTeX editor inspired by [OpenPrism](https://github.com/OpenDCAI/OpenPrism) and [OpenAI Prism](https://openai.com/prism/). Write LaTeX on the left, see your compiled PDF on the right — with an AI assistant that can rewrite your document from natural language instructions.

![Dark mode split view with file tree, editor, PDF preview, and AI panel]

## Features

- **Split view** — LaTeX source editor alongside live PDF preview
- **File tree** — open and manage an entire project folder with multiple files
- **Multi-tab editor** — open several `.tex` files at once, with unsaved-change indicators
- **One-click compile** — `⌘+Enter` saves and compiles via `pdflatex`
- **AI assistant** — describe a change in plain English; Claude rewrites your LaTeX and lets you Apply or Discard
- **Streaming AI responses** — output appears word by word, just like a chat interface
- **Light / Dark mode** — toggle in the top bar, preference saved across sessions
- **Resizable panes** — drag any panel border to adjust widths
- **Right-click context menu** — rename or delete files directly from the tree

## Requirements

### Python
Python 3.8 or later. Check with:
```bash
python3 --version
```

### LaTeX
BasicTeX (lightweight, ~140 MB) or full MacTeX (~5 GB):

```bash
# Recommended: BasicTeX
brew install --cask basictex

# After installing, reload your PATH:
eval "$(/usr/libexec/path_helper)"
```

If your document uses extra packages (e.g. `acmart`, `beamer`), install them with:
```bash
sudo tlmgr update --self
sudo tlmgr install <package-name>
```

Common packages:
```bash
sudo tlmgr install acmart beamer biblatex collection-fontsrecommended
```

### AI assistant (optional)
An [Anthropic API key](https://console.anthropic.com) — paste it into Settings (⚙) inside the editor. The key is stored locally in your browser and never sent anywhere except `api.anthropic.com`.

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/latex-editor.git
cd latex-editor
bash run.sh
```

The launcher will:
1. Create a Python virtual environment
2. Install `flask` and `anthropic` automatically
3. Open `http://localhost:8080` in your browser

## Usage

### Open a project folder
By default the editor opens the `project/` folder inside the repo. To open your own folder:

```bash
bash run.sh /path/to/my/paper
```

### Keyboard shortcuts
| Shortcut | Action |
|---|---|
| `⌘ Enter` | Compile current file |
| `⌘ S` | Save current file |
| `⌘ K` | Toggle AI assistant panel |

### AI assistant
1. Click the **⌘K** button (top right) or press `⌘K` to open the AI panel
2. Enter your Anthropic API key in **Settings (⚙)** if you haven't already
3. Type an instruction, e.g.:
   - *"Add a table of contents"*
   - *"Change the font size to 12pt"*
   - *"Add a bibliography section with BibTeX"*
   - *"Convert the itemize list to a numbered list"*
4. Click **Apply** to replace your source with the AI's version — it compiles automatically

### File management
- **New file / folder** — use the `+` buttons in the file tree header
- **Rename / Delete** — right-click any file or folder
- Files with unsaved changes show a `•` dot on their tab

## Project structure

```
latex-editor/
├── app.py              # Flask server (compile, file API, AI streaming)
├── run.sh              # One-click launcher
├── templates/
│   └── index.html      # Full editor UI (single-file, no build step)
├── project/            # Default project folder (your .tex files go here)
└── README.md
```

## Troubleshooting

**`pdflatex not found`**
BasicTeX was installed but the PATH hasn't updated. Run:
```bash
eval "$(/usr/libexec/path_helper)"
```
Then restart the server.

**`File 'somepackage.cls' not found`**
Install the missing package:
```bash
sudo tlmgr install somepackage
```

**Port already in use**
macOS AirPlay uses port 5000. The editor runs on **8080** by default. If 8080 is also taken, edit the last line of `app.py` and change `port=8080`.

**AI returns an error**
Check that your API key is correct in Settings (⚙). Keys start with `sk-ant-`.

## License

MIT
