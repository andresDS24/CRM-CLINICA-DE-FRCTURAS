# CRM Clínica de Ortopedia

Este proyecto implementa un CRM básico para la gestión de aseguradoras y contratos en una clínica especializada.

## Versiones disponibles
- API backend: FastAPI (en `main.py`)
- Visualización interactiva: Streamlit (en `app.py`)

## Requisitos
```bash
pip install fastapi uvicorn sqlalchemy pydantic streamlit pandas
```

## Ejecución del sistema
- API backend:
```bash
uvicorn main:app --reload
```
- Interfaz Streamlit:
```bash
streamlit run app.py
```

## Endpoints estratégicos (FastAPI)
- `/informes/total-por-aseguradora/`: contratos y techo acumulado por aseguradora
- `/informes/vencimientos-proximos/`: contratos que vencen en los próximos 30 días

## Funcionalidades Streamlit
- Ver contratos y aseguradoras
- Generar informes estratégicos
- Agregar aseguradoras vía formulario
