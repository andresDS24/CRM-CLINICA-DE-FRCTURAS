# Dashboard de Seguimiento de Proyectos por Procesos y Subprocesos

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(page_title="Gestor de Proyectos", layout="wide")
st.title("📊 Dashboard de Seguimiento de Proyectos")

engine = create_engine("sqlite:///seguimiento.db")

with engine.begin() as conn:
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
        proceso_id INTEGER
    );
    """))
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        responsable TEXT,
        estado TEXT,
        proceso_id INTEGER,
        subproceso_id INTEGER
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
        estado TEXT
    );
    """))

@st.cache_data

def cargar_datos():
    procesos = pd.read_sql("SELECT * FROM procesos", engine)
    subprocesos = pd.read_sql("SELECT * FROM subprocesos", engine)
    proyectos = pd.read_sql("SELECT * FROM proyectos", engine)
    tareas = pd.read_sql("SELECT * FROM tareas", engine)
    return procesos, subprocesos, proyectos, tareas

procesos, subprocesos, proyectos, tareas = cargar_datos()

menu = st.sidebar.radio("Navegación", ["Registrar", "Visualizar", "Editar/Eliminar"])

if menu == "Registrar":
    st.sidebar.subheader("➕ Registro de Procesos y Subprocesos")
    with st.sidebar.form("form_proceso"):
        nuevo_proceso = st.text_input("Nuevo proceso")
        nuevo_subproceso = st.text_input("Subproceso del proceso")
        submit_proc = st.form_submit_button("Guardar proceso y subproceso")
        if submit_proc and nuevo_proceso:
            proceso_existente = pd.read_sql("SELECT * FROM procesos WHERE nombre = :nombre", engine, params={"nombre": nuevo_proceso})
            if proceso_existente.empty:
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO procesos (nombre) VALUES (:nombre)"), {"nombre": nuevo_proceso})
                    proc_id = pd.read_sql("SELECT id FROM procesos WHERE nombre = :nombre", engine, params={"nombre": nuevo_proceso})['id'].iloc[0]
                    if nuevo_subproceso:
                        conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id) VALUES (:nombre, :proc_id)"), {"nombre": nuevo_subproceso, "proc_id": proc_id})
                st.success("Proceso y subproceso guardados.")
                st.cache_data.clear()
                st.experimental_rerun()
            else:
                st.warning("⚠️ El proceso ya existe.")

    st.sidebar.subheader("📁 Registro de Proyectos")
    with st.sidebar.form("form_proyecto"):
        nombre_proy = st.text_input("Nombre del proyecto")
        responsable_proy = st.text_input("Responsable")
        estado_proy = st.selectbox("Estado", ["Pendiente", "En curso", "Finalizado"])
        proc_sel = st.selectbox("Proceso", procesos['nombre'] if not procesos.empty else [])
        subproc_sel = st.selectbox("Subproceso", subprocesos['nombre'] if not subprocesos.empty else [])
        submit_proy = st.form_submit_button("Guardar proyecto")
        if submit_proy and nombre_proy and not procesos.empty and not subprocesos.empty:
            proc_id = procesos.loc[procesos['nombre'] == proc_sel, 'id'].values[0]
            subproc_id = subprocesos.loc[subprocesos['nombre'] == subproc_sel, 'id'].values[0]
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO proyectos (nombre, responsable, estado, proceso_id, subproceso_id)
                    VALUES (:nombre, :resp, :estado, :pid, :spid)
                """), {"nombre": nombre_proy, "resp": responsable_proy, "estado": estado_proy, "pid": proc_id, "spid": subproc_id})
            st.success("Proyecto registrado.")
            st.cache_data.clear()
            st.experimental_rerun()

    st.sidebar.subheader("📝 Registro de Tareas")
    with st.sidebar.form("form_tarea"):
        proyectos_disp = proyectos['nombre'].tolist() if not proyectos.empty else []
        proyecto_sel = st.selectbox("Proyecto", proyectos_disp)
        descripcion = st.text_area("Descripción")
        responsable = st.text_input("Responsable")
        fecha_ini = st.date_input("Fecha inicio", value=pd.to_datetime("today"))
        fecha_fin = st.date_input("Fecha fin", value=pd.to_datetime("today"))
        estado = st.selectbox("Estado", ["Pendiente", "En curso", "Finalizada"])
        submit_tarea = st.form_submit_button("Guardar tarea")
        if submit_tarea and proyecto_sel:
            proyecto_id = proyectos.loc[proyectos['nombre'] == proyecto_sel, 'id'].values[0]
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO tareas (proyecto_id, descripcion, responsable, fecha_inicio, fecha_fin, estado)
                    VALUES (:pid, :desc, :resp, :ini, :fin, :estado)
                """), {
                    "pid": proyecto_id,
                    "desc": descripcion,
                    "resp": responsable,
                    "ini": fecha_ini.strftime("%Y-%m-%d"),
                    "fin": fecha_fin.strftime("%Y-%m-%d"),
                    "estado": estado
                })
            st.success("Tarea registrada.")
            st.cache_data.clear()
            st.experimental_rerun()
