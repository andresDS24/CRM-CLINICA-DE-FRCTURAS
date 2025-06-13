
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(page_title="Configuración de Procesos", layout="wide")
st.title("⚙️ Panel de Configuración Jerárquica de Procesos y Subprocesos")

engine = create_engine("sqlite:///configuracion.db")

# Crear tablas
with engine.begin() as conn:
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS procesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            fecha_creacion TEXT
        )
    '''))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS subprocesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            proceso_id INTEGER,
            fecha_creacion TEXT
        )
    '''))

@st.cache_data
def cargar_datos():
    procesos = pd.read_sql("SELECT * FROM procesos", engine)
    subprocesos = pd.read_sql("SELECT * FROM subprocesos", engine)
    return procesos, subprocesos

procesos, subprocesos = cargar_datos()

tab1, tab2 = st.tabs(["🧱 Procesos", "🔗 Subprocesos"])

with tab1:
    st.subheader("Gestión de Procesos")
    with st.form("crear_proceso"):
        nuevo_proceso = st.text_input("Nombre del nuevo proceso")
        if st.form_submit_button("Crear proceso") and nuevo_proceso:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO procesos (nombre, fecha_creacion) VALUES (:n, :f)"),
                             {"n": nuevo_proceso, "f": datetime.now().isoformat()})
            st.cache_data.clear()
            st.success("Proceso creado con éxito.")
            st.rerun()

    st.write("### Procesos existentes")
    for _, row in procesos.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"🔹 **{row['nombre']}**")
        with col2:
            if st.button("🗑️ Eliminar", key=f"del_proc_{row['id']}"):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM procesos WHERE id = :id"), {"id": row['id']})
                st.cache_data.clear()
                st.rerun()

with tab2:
    st.subheader("Gestión de Subprocesos")
    if procesos.empty:
        st.warning("Primero debe crear al menos un proceso.")
    else:
        with st.form("crear_subproceso"):
            proc_opciones = procesos['nombre'].tolist()
            proc_sel = st.selectbox("Proceso asociado", proc_opciones)
            nuevo_subproc = st.text_input("Nombre del subproceso")
            if st.form_submit_button("Crear subproceso") and nuevo_subproc:
                pid = procesos[procesos['nombre'] == proc_sel]['id'].iloc[0]
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id, fecha_creacion) VALUES (:n, :p, :f)"),
                                 {"n": nuevo_subproc, "p": pid, "f": datetime.now().isoformat()})
                st.cache_data.clear()
                st.success("Subproceso creado con éxito.")
                st.rerun()

        st.write("### Subprocesos por proceso")
        for _, proc in procesos.iterrows():
            hijos = subprocesos[subprocesos['proceso_id'] == proc['id']]
            with st.expander(f"🔸 {proc['nombre']} ({len(hijos)} subprocesos)"):
                for _, sub in hijos.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"↪️ {sub['nombre']}")
                    with col2:
                        if st.button("Eliminar", key=f"del_sub_{sub['id']}"):
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM subprocesos WHERE id = :id"), {"id": sub['id']})
                            st.cache_data.clear()
                            st.rerun()
