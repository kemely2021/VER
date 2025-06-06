import os
import zipfile
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from concurrent.futures import ProcessPoolExecutor
import chardet
import shutil
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')


def analyze_txt_file(filepath):
    result = {}
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read()
            size_kb = len(raw_data) / 1024
            encoding = chardet.detect(raw_data)['encoding'] or "unknown"
            df = pd.read_csv(pd.io.common.BytesIO(raw_data), encoding=encoding)
            num_rows = len(df)
            cols = list(df.columns)
            if num_rows < 10:
                granularity = "baja"
            elif num_rows < 50:
                granularity = "media"
            else:
                granularity = "alta"
            result = {
                "columns": cols,
                "encoding": encoding,
                "granularity": granularity,
                "num_rows": num_rows,
                "size_kb": round(size_kb, 2)
            }
    except Exception as e:
        result = {"error": str(e)}
    return os.path.basename(filepath), result

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/packing')
def packing_page():
    return send_from_directory('static', 'packing.html')

@app.route('/info')
def info_page():
    return send_from_directory('static', 'gtfs_info.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/upload', methods=['POST'])
def upload_gtfs():
    print(">>> Se recibió una solicitud a /upload")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        base_name = os.path.splitext(file.filename)[0].replace(" ", "_").replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"tmp_{base_name}_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        print(f">>> Extrayendo ZIP en: {temp_dir}")

        with zipfile.ZipFile(file) as z:
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            z.extractall(temp_dir, members=txt_files)

        txt_paths = [os.path.join(temp_dir, f) for f in txt_files]

        print(f">>> Archivos extraídos: {txt_paths}")

        results = {}
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(analyze_txt_file, path) for path in txt_paths]
            for future in futures:
                filename, res = future.result()
                results[filename] = res

        print(">>> Procesamiento exitoso")
        shutil.rmtree(temp_dir)
        print(f">>> Carpeta temporal eliminada: {temp_dir}")

        return jsonify(results)

    except zipfile.BadZipFile:
        return jsonify({"error": "Archivo ZIP inválido"}), 400
    except Exception as e:
        print(f">>> Error inesperado: {str(e)}")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
