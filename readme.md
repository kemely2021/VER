# Visualizador GTFS con Flask y D3.js

Este proyecto permite subir un archivo ZIP con datos GTFS, procesarlos con Python (pandas + Flask) y mostrar información básica de las tablas y sus columnas en una página web con D3.js.

---

## Requisitos

- Python 3.x
- pip (gestor de paquetes de Python)

---

## Instalación

1. Clona o descarga este proyecto y navega a la carpeta raíz.

2. (Opcional) Crea y activa un entorno virtual:

Instala las dependencias:

## Activa tu entorno virtual:
env\Scripts\activate 

## Instala las dependencias
pip install -r requirements.txt

## Ejecuta el servidor
python app.py


## Como solucionar 

Estructura del proyecto
php
Copiar
Editar
V1/
│
├── app.py                # Backend Flask para procesar el ZIP
├── requirements.txt      # Dependencias del proyecto
├── static/
│   ├── index.html        # Página web con formulario y D3.js
│   └── script.js         # Visualización con D3.js
└── uploads/              # (Opcional) Carpeta para archivos subidos


env\Scripts\activate.bat


## Verlo en web
http://localhost:5000/

