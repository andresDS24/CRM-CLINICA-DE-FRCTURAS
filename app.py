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
CREATE TABLE IF NOT EXISTS subprocesos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    proceso_id INTEGER,
    fecha_creacion TEXT
);

    );
    """))
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS subprocesos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        subproceso_id INTEGER,
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

@st.cache_data
def cargar_datos():
    procesos = pd.read_sql("SELECT * FROM procesos", engine)
    subprocesos = pd.read_sql("SELECT * FROM subprocesos", engine)
    proyectos = pd.read_sql("SELECT * FROM proyectos", engine)
    tareas = pd.read_sql("SELECT * FROM tareas", engine)
    return procesos, subprocesos, proyectos, tareas

procesos, subprocesos, proyectos, tareas = cargar_datos()

st.sidebar.header("🧩 Gestión Jerárquica")

# Procesos
st.sidebar.subheader("Procesos")
nuevo_proc = st.sidebar.text_input("Nuevo Proceso")
if st.sidebar.button("Crear Proceso") and nuevo_proc:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO procesos (nombre, fecha_creacion) VALUES (:n, :f)"), {"n": nuevo_proc, "f": datetime.now().isoformat()})
    st.cache_data.clear()
    procesos, subprocesos, proyectos, tareas = cargar_datos()
    st.rerun()

proc_sel = st.sidebar.selectbox("Seleccionar Proceso", procesos['nombre'].tolist() if not procesos.empty else [])
if st.sidebar.button("Eliminar Proceso") and proc_sel:
    with engine.begin() as conn:
        pid = procesos[procesos['nombre'] == proc_sel]['id'].values[0]
        conn.execute(text("DELETE FROM procesos WHERE id = :pid"), {"pid": pid})
    st.cache_data.clear()
    procesos, subprocesos, proyectos, tareas = cargar_datos()
    st.rerun()

# Subprocesos
st.sidebar.subheader("Subprocesos")
subproc_df = pd.DataFrame()
if proc_sel:
    proc_id = procesos[procesos['nombre'] == proc_sel]['id'].values[0]
    subproc_df = subprocesos[subprocesos['proceso_id'] == proc_id]

nuevo_subproc = st.sidebar.text_input("Nuevo Subproceso")
if st.sidebar.button("Crear Subproceso") and nuevo_subproc and proc_sel:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id, fecha_creacion) VALUES (:n, :pid, :f)"), {"n": nuevo_subproc, "pid": proc_id, "f": datetime.now().isoformat()})
    st.cache_data.clear()
    procesos, subprocesos, proyectos, tareas = cargar_datos()
    st.rerun()

subproc_sel = st.sidebar.selectbox("Seleccionar Subproceso", subproc_df['nombre'].tolist() if not subproc_df.empty else [])
if st.sidebar.button("Eliminar Subproceso") and subproc_sel:
    spid = subproc_df[subproc_df['nombre'] == subproc_sel]['id'].values[0]
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM subprocesos WHERE id = :spid"), {"spid": spid})
    st.cache_data.clear()
    procesos, subprocesos, proyectos, tareas = cargar_datos()
    st.rerun()

# Proyectos
st.sidebar.subheader("Proyectos")
nombre_proy = st.sidebar.text_input("Nombre Proyecto")
responsable_proy = st.sidebar.text_input("Responsable Principal")
fecha_proy = st.sidebar.date_input("Fecha Proyectada")
if st.sidebar.button("Crear Proyecto") and nombre_proy and proc_sel and subproc_sel:
    pid = procesos[procesos['nombre'] == proc_sel]['id'].values[0]
    spid = subprocesos[subprocesos['nombre'] == subproc_sel]['id'].values[0]
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO proyectos (nombre, responsable, estado, proceso_id, subproceso_id, fecha_creacion, fecha_proyeccion)
            VALUES (:n, :r, 'Pendiente', :pid, :spid, :f, :p)"""),
            {"n": nombre_proy, "r": responsable_proy, "pid": pid, "spid": spid, "f": datetime.now().isoformat(), "p": fecha_proy.isoformat()})
    st.cache_data.clear()
    procesos, subprocesos, proyectos, tareas = cargar_datos()
    st.rerun()

proy_df = pd.DataFrame()
if subproc_sel:
    spid = subprocesos[subprocesos['nombre'] == subproc_sel]['id'].values[0]
    proy_df = proyectos[proyectos['subproceso_id'] == spid]

proy_sel = st.sidebar.selectbox("Seleccionar Proyecto", proy_df['nombre'].tolist() if not proy_df.empty else [])

# Tareas
st.sidebar.subheader("Tareas")
desc = st.sidebar.text_area("Descripción")
resp = st.sidebar.text_input("Responsable")
fini = st.sidebar.date_input("Inicio")
ffin = st.sidebar.date_input("Fin")
fproy = st.sidebar.date_input("Fecha Proyección")
if st.sidebar.button("Crear Tarea") and proy_sel:
    prid = proyectos[proyectos['nombre'] == proy_sel]['id'].values[0]
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO tareas (proyecto_id, descripcion, responsable, fecha_inicio, fecha_fin, estado, fecha_creacion, fecha_proyeccion)
            VALUES (:pid, :d, :r, :i, :f, 'Pendiente', :fc, :fp)"""),
            {"pid": prid, "d": desc, "r": resp, "i": fini.isoformat(), "f": ffin.isoformat(), "fc": datetime.now().isoformat(), "fp": fproy.isoformat()})
    st.cache_data.clear()
    procesos, subprocesos, proyectos, tareas = cargar_datos()
    st.rerun()

# Visualización
st.header("📌 Seguimiento Visual")
if tareas.empty:
    st.info("No hay tareas disponibles.")
else:
    tareas['fecha_inicio'] = pd.to_datetime(tareas['fecha_inicio'])
    tareas['fecha_fin'] = pd.to_datetime(tareas['fecha_fin'])
    gantt = px.timeline(tareas, x_start='fecha_inicio', x_end='fecha_fin', y='descripcion', color='estado')
    gantt.update_yaxes(autorange='reversed')
    st.plotly_chart(gantt, use_container_width=True)

    tareas['fecha_proyeccion'] = pd.to_datetime(tareas['fecha_proyeccion'])
    tareas['desviacion'] = (tareas['fecha_fin'] - tareas['fecha_proyeccion']).dt.days

    dev = px.bar(tareas, x='descripcion', y='desviacion', color='estado')
    st.plotly_chart(dev, use_container_width=True)

    resumen = tareas.groupby(['proyecto_id', 'estado']).size().unstack(fill_value=0).reset_index()
    resumen = resumen.merge(proyectos, left_on='proyecto_id', right_on='id')
    resumen['Total'] = resumen[['Pendiente', 'En curso', 'Finalizada']].sum(axis=1)
    resumen['Avance %'] = (resumen['Finalizada'] / resumen['Total'] * 100).round(1)
    st.dataframe(resumen[['nombre', 'responsable', 'Pendiente', 'En curso', 'Finalizada', 'Avance %']])

    if st.button("✅ Finalizar Proyecto") and proy_sel:
        prid = proyectos[proyectos['nombre'] == proy_sel]['id'].values[0]
        with engine.begin() as conn:
            conn.execute(text("UPDATE proyectos SET estado = 'Finalizado', fecha_finalizacion = :f WHERE id = :id"),
                         {"f": datetime.now().isoformat(), "id": prid})
        st.success("Proyecto Finalizado")
        st.cache_data.clear()
        procesos, subprocesos, proyectos, tareas = cargar_datos()
        st.rerun()
