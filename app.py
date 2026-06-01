#!/usr/bin/env python3
"""
Local LaTeX Editor - OpenPrism inspired split-view editor
Run: python3 app.py
Then open: http://localhost:5000
"""

import os
import subprocess
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compile', methods=['POST'])
def compile_latex():
    data = request.get_json()
    latex_code = data.get('code', '')

    if not latex_code.strip():
        return jsonify({'error': 'No LaTeX code provided'}), 400

    # Create a temp directory for compilation
    tmpdir = tempfile.mkdtemp()
    tex_file = os.path.join(tmpdir, 'main.tex')
    pdf_file = os.path.join(tmpdir, 'main.pdf')

    try:
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_code)

        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', tmpdir, tex_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        if os.path.exists(pdf_file):
            # Copy PDF to a stable path
            out_pdf = os.path.join(tempfile.gettempdir(), 'latex_output.pdf')
            shutil.copy(pdf_file, out_pdf)
            return jsonify({'success': True, 'pdf_url': '/pdf'})
        else:
            # Extract error from log
            log = result.stdout + result.stderr
            error_lines = [l for l in log.split('\n') if l.startswith('!') or 'Error' in l]
            error_msg = '\n'.join(error_lines[:10]) if error_lines else log[-1000:]
            return jsonify({'success': False, 'error': error_msg})

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Compilation timed out (30s limit)'}), 500
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'pdflatex not found. Please install MacTeX: https://www.tug.org/mactex/'}), 500
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

@app.route('/pdf')
def serve_pdf():
    pdf_path = os.path.join(tempfile.gettempdir(), 'latex_output.pdf')
    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype='application/pdf')
    return 'No PDF compiled yet', 404

if __name__ == '__main__':
    print("=" * 50)
    print("  LaTeX Editor running at http://localhost:8080")
    print("=" * 50)
    app.run(debug=False, port=8080)
