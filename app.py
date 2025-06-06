import os, zipfile, shutil
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import chardet
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS                            # ← NUEVO

# ───────────── Config básica ─────────────
app = Flask(__name__)
CORS(app)                                              # ← NUEVO
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Variables para vista previa
last_extract_dir = None
files_cache      = {}

# ───────────── Rutas estáticas ───────────
@app.route('/')
def root():             return send_from_directory('.', 'index.html')

@app.route('/packing')
def packing_page():     return send_from_directory('static', 'packing.html')

@app.route('/info')
def info_page():        return send_from_directory('static', 'gtfs_info.html')

@app.route('/static/<path:path>')
def static_files(path): return send_from_directory('static', path)


# ───────────── Util: resumir un TXT ──────
def analyze_txt_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
        size_kb  = len(raw) / 1024
        enc      = chardet.detect(raw)['encoding'] or 'utf-8'
        df       = pd.read_csv(pd.io.common.BytesIO(raw),
                               encoding=enc, dtype=str, low_memory=False)
        num_rows = len(df)
        gran     = 'baja' if num_rows < 10 else 'media' if num_rows < 50 else 'alta'
        result   = {
            'columns': list(df.columns),
            'encoding': enc,
            'granularity': gran,
            'num_rows': num_rows,
            'size_kb': round(size_kb, 2)
        }
    except Exception as e:
        result = {'error': str(e)}
    return os.path.basename(filepath), result


# ───────────── /upload ─────────────
@app.route('/upload', methods=['POST'])
def upload_gtfs():
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'error': 'No se adjuntó archivo'}), 400

    file = request.files['file']
    try:
        base = os.path.splitext(file.filename)[0].replace(' ', '_').replace('.', '_')
        tmp  = datetime.now().strftime('%Y%m%d_%H%M')
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'tmp_{base}_{tmp}')
        os.makedirs(temp_dir, exist_ok=True)

        with zipfile.ZipFile(file) as z:
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            z.extractall(temp_dir, members=txt_files)

        paths = [os.path.join(temp_dir, f) for f in txt_files]
        results = {}
        with ProcessPoolExecutor() as exe:
            for filename, res in exe.map(analyze_txt_file, paths):
                results[filename] = res

        # registra carpeta para /preview
        global last_extract_dir, files_cache
        last_extract_dir = temp_dir
        files_cache = {}

        return jsonify(results)

    except zipfile.BadZipFile:
        return jsonify({'error': 'Archivo ZIP inválido'}), 400
    except Exception as e:
        return jsonify({'error': f'Error inesperado: {e}'}), 500


# ───────────── /preview/<archivo> ────────
@app.route('/preview/<path:filename>')
def preview_file(filename):
    global last_extract_dir, files_cache
    if not last_extract_dir:
        return jsonify({'error': 'Primero sube un feed GTFS'}), 400

    if filename not in files_cache:
        fpath = os.path.join(last_extract_dir, filename)
        if not os.path.exists(fpath):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        try:
            enc = chardet.detect(open(fpath, 'rb').read())['encoding'] or 'utf-8'
            df  = pd.read_csv(fpath, encoding=enc, dtype=str, low_memory=False)
            files_cache[filename] = df.head(100).to_dict(orient='records')
        except Exception as e:
            return jsonify({'error': f'No se pudo leer {filename}: {e}'}), 500

    return jsonify(files_cache[filename])


# ───────────── Local dev only ────────────
if __name__ == '__main__':
    app.run(debug=True)
