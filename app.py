# CRM para clínica de ortopedia con contratos aseguradores – versión Streamlit + FastAPI backend + Módulo de Proyectos y Seguimiento + Gráficas + Gestión de Procesos + Alertas + Compatibilidad Android + Integración Calendar

# Archivo: app.py (Streamlit frontend)
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuración para mejor visualización en móviles
st.set_page_config(page_title="CRM Clínica de Ortopedia", layout="centered")
st.title("📋 CRM Clínica de Ortopedia")

engine = create_engine("sqlite:///crm_clinica.db")

# --- Crear tablas si no existen ---
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS aseguradoras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            nit TEXT,
            contacto TEXT
        );
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            tipo_tarifa TEXT,
            techo_mensual REAL,
            condiciones TEXT,
            aseguradora_id INTEGER
        );
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS procesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT
        );
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS subprocesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            proceso_id INTEGER,
            FOREIGN KEY (proceso_id) REFERENCES procesos(id)
        );
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            area TEXT,
            responsable TEXT,
            estado TEXT,
            proceso_id INTEGER,
            subproceso_id INTEGER,
            FOREIGN KEY (proceso_id) REFERENCES procesos(id),
            FOREIGN KEY (subproceso_id) REFERENCES subprocesos(id)
        );
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            descripcion TEXT,
            responsable TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            estado TEXT,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id)
        );
    """))

@st.cache_data
def cargar_datos():
    aseguradoras = pd.read_sql("SELECT * FROM aseguradoras", engine)
    contratos = pd.read_sql("SELECT * FROM contratos", engine)
    proyectos = pd.read_sql("SELECT * FROM proyectos", engine)
    tareas = pd.read_sql("SELECT * FROM tareas", engine)
    procesos = pd.read_sql("SELECT * FROM procesos", engine)
    subprocesos = pd.read_sql("SELECT * FROM subprocesos", engine)
    return aseguradoras, contratos, proyectos, tareas, procesos, subprocesos

aseguradoras, contratos, proyectos, tareas, procesos, subprocesos = cargar_datos()

# --- Filtros globales ---
st.sidebar.title("Filtros Interactivos")
proceso_filtrado = st.sidebar.multiselect("Filtrar por proceso", procesos.nombre.unique())
responsable_filtrado = st.sidebar.multiselect("Filtrar por responsable", tareas.responsable.unique())
fecha_inicio_filtro = st.sidebar.date_input("Desde", [])
fecha_fin_filtro = st.sidebar.date_input("Hasta", [])

# --- Informes de avance ---
with st.sidebar.expander("Resumen de avance por proyecto"):
    tareas_estado = tareas.groupby(['proyecto_id', 'estado']).size().unstack(fill_value=0).reset_index()
    tareas_estado = tareas_estado.merge(proyectos[['id', 'nombre']], left_on='proyecto_id', right_on='id')
    tareas_estado['total'] = tareas_estado[['Pendiente','En curso','Finalizada']].sum(axis=1, skipna=True)
    tareas_estado['avance'] = (tareas_estado['Finalizada'] / tareas_estado['total'] * 100).round(1)
    for i, row in tareas_estado.iterrows():
        color = "🟩" if row['avance'] >= 80 else ("🟨" if row['avance'] >= 40 else "🟥")
        st.markdown(f"{color} **{row['nombre']}** → {row['avance']}% completado")

# --- Alertas automatizadas ---
with st.sidebar.expander("🔔 Alertas de vencimientos"):
    hoy = datetime.today()
    tareas['fecha_fin_dt'] = pd.to_datetime(tareas['fecha_fin'], errors='coerce')
    proximas_tareas = tareas[(tareas['fecha_fin_dt'] >= hoy) & (tareas['fecha_fin_dt'] <= hoy + timedelta(days=7))]
    for _, row in proximas_tareas.iterrows():
        st.error(f"📅 {row['descripcion']} (Responsable: {row['responsable']}) vence el {row['fecha_fin']}")

    if st.button("📆 Sincronizar con Google Calendar"):
        try:
            scope = ["https://www.googleapis.com/auth/calendar"]
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcal_credentials"], scopes=scope
            )
            service = build("calendar", "v3", credentials=credentials)
            calendar_id = "primary"
            for _, row in proximas_tareas.iterrows():
                event = {
                    'summary': row['descripcion'],
                    'description': f"Responsable: {row['responsable']} | Proyecto ID: {row['proyecto_id']}",
                    'start': {'dateTime': f"{row['fecha_fin']}T08:00:00", 'timeZone': 'America/Bogota'},
                    'end': {'dateTime': f"{row['fecha_fin']}T09:00:00", 'timeZone': 'America/Bogota'}
                }
                service.events().insert(calendarId=calendar_id, body=event).execute()
            st.success("Eventos sincronizados con Google Calendar")
        except Exception as e:
            st.error(f"Error al sincronizar: {e}")

with st.sidebar.expander("📱 Instalar en Android"):
    st.info("Puedes instalar esta app como aplicación desde Chrome > Agregar a pantalla de inicio")
