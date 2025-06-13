
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(page_title="Gestor de Proyectos", layout="wide")
st.title("📊 Dashboard de Seguimiento de Proyectos")

engine = create_engine("sqlite:///seguimiento.db")

# Crear tablas
with engine.begin() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS procesos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        fecha_creacion TEXT
    );
    """))
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS subprocesos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        proceso_id INTEGER,
        fecha_creacion TEXT
    );
    """))
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        responsable TEXT,
        estado TEXT,
        proceso_id INTEGER,
        subproceso_id INTEGER,
        fecha_creacion TEXT,
        fecha_proyeccion TEXT,
        fecha_finalizacion TEXT
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
        fecha_creacion TEXT,
        fecha_proyeccion TEXT,
        fecha_cumplimiento TEXT
    );
    """))

st.success("✅ Base de datos creada correctamente. Ahora puedes continuar desarrollando tu dashboard.")
