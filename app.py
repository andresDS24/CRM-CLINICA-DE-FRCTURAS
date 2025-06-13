
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(page_title="Dashboard de Proyectos", layout="wide")
st.title("📊 Dashboard de Seguimiento de Proyectos")

engine = create_engine("sqlite:///seguimiento.db")

# Crear tablas si no existen
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

@st.cache_data
def cargar():
    return (
        pd.read_sql("SELECT * FROM procesos", engine),
        pd.read_sql("SELECT * FROM subprocesos", engine),
        pd.read_sql("SELECT * FROM proyectos", engine),
        pd.read_sql("SELECT * FROM tareas", engine)
    )

procesos, subprocesos, proyectos, tareas = cargar()

tab1, tab2 = st.tabs(["⚙️ Configuración", "📈 Visualización"])

with tab1:
    st.subheader("➕ Crear Proceso y Subproceso")
    with st.form("crear_proceso"):
        nuevo_proc = st.text_input("Nombre del Proceso")
        nuevo_sub = st.text_input("Nombre del Subproceso")
        submit = st.form_submit_button("Crear")
        if submit and nuevo_proc:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO procesos (nombre, fecha_creacion) VALUES (:n, :f)"),
                             {"n": nuevo_proc, "f": datetime.now().isoformat()})
            procesos, subprocesos, proyectos, tareas = cargar()
            if nuevo_sub:
                proc_id = procesos[procesos['nombre'] == nuevo_proc]['id'].iloc[0]
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id, fecha_creacion) VALUES (:n, :p, :f)"),
                                 {"n": nuevo_sub, "p": proc_id, "f": datetime.now().isoformat()})
            st.success("Proceso y/o subproceso creado correctamente.")
            st.cache_data.clear()
            st.rerun()

    st.subheader("📁 Crear Proyecto y Tareas")
    if procesos.empty or subprocesos.empty:
        st.warning("Debe crear al menos un proceso y un subproceso.")
    else:
        proc_sel = st.selectbox("Proceso", procesos['nombre'])
        sub_df = subprocesos[subprocesos['proceso_id'] == procesos[procesos['nombre'] == proc_sel]['id'].iloc[0]]
        sub_sel = st.selectbox("Subproceso", sub_df['nombre'])
        with st.form("crear_proy"):
            nombre = st.text_input("Nombre del Proyecto")
            resp = st.text_input("Responsable")
            fproy = st.date_input("Fecha Proyección")
            crear = st.form_submit_button("Crear Proyecto")
            if crear:
                pid = procesos[procesos['nombre'] == proc_sel]['id'].iloc[0]
                spid = sub_df[sub_df['nombre'] == sub_sel]['id'].iloc[0]
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO proyectos (nombre, responsable, estado, proceso_id, subproceso_id, fecha_creacion, fecha_proyeccion)
                        VALUES (:n, :r, 'Pendiente', :pid, :spid, :f, :fp)
                    """), {"n": nombre, "r": resp, "pid": pid, "spid": spid,
                            "f": datetime.now().isoformat(), "fp": fproy.isoformat()})
                st.success("Proyecto creado")
                st.cache_data.clear()
                st.rerun()

    st.subheader("📝 Crear Tareas")
    proy_disp = proyectos['nombre'].tolist()
    if proy_disp:
        proy_sel = st.selectbox("Proyecto", proy_disp)
        with st.form("crear_tarea"):
            desc = st.text_area("Descripción")
            resp = st.text_input("Responsable tarea")
            fi = st.date_input("Fecha inicio")
            ff = st.date_input("Fecha fin")
            fp = st.date_input("Fecha proyección")
            crear_tarea = st.form_submit_button("Crear Tarea")
            if crear_tarea:
                prid = proyectos[proyectos['nombre'] == proy_sel]['id'].iloc[0]
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO tareas (proyecto_id, descripcion, responsable, fecha_inicio, fecha_fin, estado, fecha_creacion, fecha_proyeccion)
                        VALUES (:pid, :d, :r, :i, :f, 'Pendiente', :fc, :fp)
                    """), {"pid": prid, "d": desc, "r": resp, "i": fi.isoformat(), "f": ff.isoformat(),
                            "fc": datetime.now().isoformat(), "fp": fp.isoformat()})
                st.success("Tarea creada")
                st.cache_data.clear()
                st.rerun()

with tab2:
    st.subheader("📊 Diagrama de Gantt y Avance")
    if tareas.empty:
        st.info("No hay tareas aún.")
    else:
        tareas['fecha_inicio'] = pd.to_datetime(tareas['fecha_inicio'], errors='coerce')
        tareas['fecha_fin'] = pd.to_datetime(tareas['fecha_fin'], errors='coerce')
        fig = px.timeline(tareas, x_start="fecha_inicio", x_end="fecha_fin", y="descripcion", color="estado")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        tareas['fecha_proyeccion'] = pd.to_datetime(tareas['fecha_proyeccion'], errors='coerce')
        tareas['desviacion'] = (tareas['fecha_fin'] - tareas['fecha_proyeccion']).dt.days
        dev = px.bar(tareas, x='descripcion', y='desviacion', color='estado', title="📉 Desviación contra Proyección")
        st.plotly_chart(dev, use_container_width=True)

        resumen = tareas.groupby(['proyecto_id', 'estado']).size().unstack(fill_value=0).reset_index()
        resumen = resumen.merge(proyectos, left_on='proyecto_id', right_on='id')
        resumen['Total'] = resumen[['Pendiente', 'En curso', 'Finalizada']].sum(axis=1)
        resumen['Avance %'] = (resumen['Finalizada'] / resumen['Total'] * 100).round(1)
        st.dataframe(resumen[['nombre', 'responsable', 'Pendiente', 'En curso', 'Finalizada', 'Avance %']])
