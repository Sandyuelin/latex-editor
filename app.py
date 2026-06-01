#!/usr/bin/env python3
"""
LaTeX Editor — Prism-inspired local editor with AI agent + folder support
Run: python3 app.py [/path/to/project]
Open: http://localhost:8080
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template, Response, stream_with_context

app = Flask(__name__)

# Ensure TeX binaries are on PATH (BasicTeX / MacTeX)
os.environ['PATH'] = '/Library/TeX/texbin:/usr/local/bin:' + os.environ.get('PATH', '')

# ── Project directory ──────────────────────────────────────────────────────────
DEFAULT_PROJECT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project')
PROJECT_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PROJECT
os.makedirs(PROJECT_DIR, exist_ok=True)

# Seed with example file if empty
_main_tex = os.path.join(PROJECT_DIR, 'main.tex')
if not os.listdir(PROJECT_DIR):
    with open(_main_tex, 'w') as f:
        f.write(r"""\documentclass[12pt]{article}
\usepackage{amsmath, amssymb, geometry}
\geometry{margin=2.5cm}

\title{My Document}
\author{Author Name}
\date{\today}

\begin{document}
\maketitle

\section{Introduction}
Welcome to the LaTeX editor.

\section{Mathematics}
\[
  e^{i\pi} + 1 = 0
\]

\end{document}
""")

def safe_path(rel):
    """Resolve rel path inside PROJECT_DIR; raise if it escapes."""
    p = Path(PROJECT_DIR) / rel
    p = p.resolve()
    if not str(p).startswith(str(Path(PROJECT_DIR).resolve())):
        raise ValueError("Path outside project")
    return p


def build_tree(root: Path):
    """Recursively build a file tree dict."""
    result = []
    try:
        entries = sorted(root.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except PermissionError:
        return result
    for entry in entries:
        if entry.name.startswith('.'):
            continue
        rel = str(entry.relative_to(PROJECT_DIR))
        if entry.is_dir():
            result.append({'name': entry.name, 'path': rel, 'type': 'dir', 'children': build_tree(entry)})
        else:
            result.append({'name': entry.name, 'path': rel, 'type': 'file'})
    return result


# ── File API ───────────────────────────────────────────────────────────────────

@app.route('/api/tree')
def api_tree():
    return jsonify({'tree': build_tree(Path(PROJECT_DIR)), 'project': PROJECT_DIR})


@app.route('/api/file', methods=['GET'])
def api_read():
    rel = request.args.get('path', '')
    try:
        p = safe_path(rel)
        return jsonify({'content': p.read_text(encoding='utf-8', errors='replace')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/file', methods=['PUT'])
def api_write():
    data = request.get_json()
    rel  = data.get('path', '')
    text = data.get('content', '')
    try:
        p = safe_path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/file', methods=['POST'])
def api_create():
    data = request.get_json()
    rel  = data.get('path', '')
    kind = data.get('type', 'file')   # 'file' | 'dir'
    try:
        p = safe_path(rel)
        if kind == 'dir':
            p.mkdir(parents=True, exist_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                p.write_text('', encoding='utf-8')
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/file', methods=['DELETE'])
def api_delete():
    rel = request.args.get('path', '')
    try:
        p = safe_path(rel)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/rename', methods=['POST'])
def api_rename():
    data    = request.get_json()
    old_rel = data.get('old', '')
    new_rel = data.get('new', '')
    try:
        src = safe_path(old_rel)
        dst = safe_path(new_rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ── Compile ────────────────────────────────────────────────────────────────────

@app.route('/compile', methods=['POST'])
def compile_latex():
    data      = request.get_json()
    latex_code = data.get('code', '')
    main_file  = data.get('mainFile', 'main.tex')   # relative path

    if not latex_code.strip():
        return jsonify({'error': 'Empty document'}), 400

    # Write the active file, then compile from PROJECT_DIR
    try:
        active = safe_path(main_file)
        active.write_text(latex_code, encoding='utf-8')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    tmpdir = tempfile.mkdtemp()
    pdf_tmp = os.path.join(tmpdir, 'out.pdf')

    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode',
             '-output-directory', tmpdir,
             str(active)],
            capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_DIR)
        )

        # Find output PDF (named after the tex file, not 'out.pdf')
        stem = active.stem
        found = os.path.join(tmpdir, stem + '.pdf')

        if os.path.exists(found):
            out = os.path.join(tempfile.gettempdir(), 'latex_output.pdf')
            shutil.copy(found, out)
            return jsonify({'success': True})
        else:
            log = result.stdout + result.stderr
            errs = [l for l in log.split('\n') if l.startswith('!') or 'Error' in l]
            return jsonify({'success': False, 'error': '\n'.join(errs[:10]) or log[-800:]})

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout (30s)'})
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'pdflatex not found.\nbrew install --cask basictex'})
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.route('/pdf')
def serve_pdf():
    p = os.path.join(tempfile.gettempdir(), 'latex_output.pdf')
    return send_file(p, mimetype='application/pdf') if os.path.exists(p) else ('No PDF yet', 404)


# ── AI ─────────────────────────────────────────────────────────────────────────

@app.route('/ai', methods=['POST'])
def ai_assist():
    data        = request.get_json()
    instruction = data.get('instruction', '')
    current_code = data.get('code', '')
    api_key     = data.get('api_key', '') or os.environ.get('ANTHROPIC_API_KEY', '')

    def sse(obj): return f"data: {json.dumps(obj)}\n\n"

    def err_stream(msg):
        yield sse({'error': msg})

    if not api_key:
        return Response(stream_with_context(err_stream('No Anthropic API key. Enter it in Settings (⚙).')),
                        mimetype='text/event-stream')

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        SYSTEM = (
            "You are an expert LaTeX assistant. The user gives you their LaTeX source and an instruction.\n"
            "Return ONLY the complete modified LaTeX — no explanations, no markdown fences, just raw LaTeX."
        )

        def generate():
            try:
                with client.messages.stream(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=8192,
                    system=SYSTEM,
                    messages=[{"role": "user",
                               "content": f"LaTeX:\n```latex\n{current_code}\n```\n\nInstruction: {instruction}"}]
                ) as stream:
                    for text in stream.text_stream:
                        yield sse({'text': text})
                yield sse({'done': True})
            except Exception as e:
                yield sse({'error': str(e)})

        return Response(stream_with_context(generate()), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
    except ImportError:
        return Response(stream_with_context(err_stream('anthropic not installed. Run: pip install anthropic')),
                        mimetype='text/event-stream')


# ── Main ───────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    print(f"\n  ✦  LaTeX Editor")
    print(f"     Project : {PROJECT_DIR}")
    print(f"     URL     : http://localhost:8080\n")
    app.run(debug=False, port=8080, threaded=True)
