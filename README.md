# CRM Clínica de Ortopedia

Este proyecto implementa un CRM básico para la gestión de aseguradoras y contratos en una clínica especializada.

## Despliegue en Streamlit Cloud
1. Sube este proyecto a un repositorio de GitHub.
2. Ingresa a https://streamlit.io/cloud y selecciona el repositorio.
3. Asegúrate de incluir `app.py` y `requirements.txt`.

## Despliegue del backend FastAPI en Render
1. Asegúrate de tener:
   - `main.py` (opcional)
   - `Procfile` con:
     web: uvicorn main:app --host=0.0.0.0 --port=10000
2. Render generará una URL pública para usar desde Streamlit.

## Requisitos
```bash
pip install -r requirements.txt
```
