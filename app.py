# Dashboard de Seguimiento de Proyectos por Procesos y Subprocesos

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(page_title="Gestor de Proyectos", layout="wide")
st.title("📊 Dashboard de Seguimiento de Proyectos")

# Conexión a base de datos SQLite
engine = create_engine("sqlite:///seguimiento.db")

# Crear tablas necesarias si no existen
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

# Cargar datos necesarios para los formularios antes de usarlos
@st.cache_data
def cargar_datos():
    procesos = pd.read_sql("SELECT * FROM procesos", engine)
    subprocesos = pd.read_sql("SELECT * FROM subprocesos", engine)
    proyectos = pd.read_sql("SELECT * FROM proyectos", engine)
    tareas = pd.read_sql("SELECT * FROM tareas", engine)
    return procesos, subprocesos, proyectos, tareas

procesos, subprocesos, proyectos, tareas = cargar_datos()

# Formularios para registrar procesos, subprocesos, proyectos y tareas
st.sidebar.subheader("➕ Registro de Procesos y Subprocesos")
with st.sidebar.form("form_proceso"):
    nuevo_proceso = st.text_input("Nuevo proceso")
    nuevo_subproceso = st.text_input("Subproceso del proceso")
    submit_proc = st.form_submit_button("Guardar proceso y subproceso")
    if submit_proc and nuevo_proceso:
        # Verificar si el proceso ya existe
        proceso_existente = pd.read_sql("SELECT * FROM procesos WHERE nombre = :nombre", engine, params={"nombre": nuevo_proceso})
        if not proceso_existente.empty:
            st.warning("⚠️ El proceso ya existe. No se puede duplicar.")
        else:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO procesos (nombre) VALUES (:nombre)"), {"nombre": nuevo_proceso})
                proc_df = pd.read_sql("SELECT id FROM procesos WHERE nombre = :nombre", engine, params={"nombre": nuevo_proceso})
                if not proc_df.empty:
                    proc_id = proc_df['id'].iloc[0]
                    if nuevo_subproceso:
                        conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id) VALUES (:nombre, :proc_id)"), {"nombre": nuevo_subproceso, "proc_id": proc_id})
                    st.success("Proceso y subproceso guardados.")
                    st.rerun()
                else:
                    st.error("❌ El proceso no se registró correctamente. Verifica si ya existe o si hubo un error de conexión.")

st.sidebar.subheader("📁 Registro de Proyectos")
with st.sidebar.form("form_proyecto"):
    nombre_proy = st.text_input("Nombre del proyecto")
    responsable_proy = st.text_input("Responsable")
    estado_proy = st.selectbox("Estado", ["Pendiente", "En curso", "Finalizado"])
    proc_sel = st.selectbox("Proceso", procesos['nombre'] if not procesos.empty else [])
    subproc_sel = st.selectbox("Subproceso", subprocesos['nombre'] if not subprocesos.empty else [])
    submit_proy = st.form_submit_button("Guardar proyecto")
    if submit_proy and nombre_proy:
        # Verificar si ya existe un proyecto con el mismo nombre
        proyecto_existente = pd.read_sql("SELECT * FROM proyectos WHERE nombre = :nombre", engine, params={"nombre": nombre_proy})
        if not proyecto_existente.empty:
            st.warning("⚠️ Ya existe un proyecto con ese nombre. No se puede duplicar.")
        else:
            proc_id = procesos.loc[procesos['nombre'] == proc_sel, 'id'].values[0]
            subproc_id = subprocesos.loc[subprocesos['nombre'] == subproc_sel, 'id'].values[0]
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO proyectos (nombre, responsable, estado, proceso_id, subproceso_id)
                    VALUES (:nombre, :resp, :estado, :pid, :spid)
                """), {"nombre": nombre_proy, "resp": responsable_proy, "estado": estado_proy, "pid": proc_id, "spid": subproc_id})
            st.success("Proyecto registrado.")
            st.rerun()

st.sidebar.subheader("📝 Registro de Tareas")

st.sidebar.subheader("⚙️ Gestión de Datos")
with st.sidebar.expander("✏️ Editar / Eliminar"):
    st.markdown("### ✍️ Edición de Proyectos")
    if not proyectos.empty:
        proyecto_editar = st.selectbox("Selecciona un proyecto para editar", proyectos['nombre'], key="edit_proy")
        nuevo_nombre = st.text_input("Nuevo nombre del proyecto", key="nuevo_nombre")
        nuevo_resp = st.text_input("Nuevo responsable", key="nuevo_resp")
        nuevo_estado = st.selectbox("Nuevo estado", ["Pendiente", "En curso", "Finalizado"], key="nuevo_estado")
        if st.button("💾 Guardar cambios en proyecto"):
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE proyectos
                    SET nombre = :nombre, responsable = :resp, estado = :estado
                    WHERE nombre = :original
                """), {"nombre": nuevo_nombre, "resp": nuevo_resp, "estado": nuevo_estado, "original": proyecto_editar})
            st.success("Proyecto actualizado correctamente")
            st.rerun()

    st.markdown("### ✍️ Edición de Tareas")
    if not tareas.empty:
        tarea_editar = st.selectbox("Selecciona una tarea para editar", tareas['descripcion'], key="edit_tarea")
        nuevo_desc = st.text_input("Nueva descripción", key="nuevo_desc")
        nuevo_resp_tarea = st.text_input("Nuevo responsable tarea", key="nuevo_resp_tarea")
        nuevo_estado_tarea = st.selectbox("Nuevo estado", ["Pendiente", "En curso", "Finalizada"], key="nuevo_estado_tarea")
        if st.button("💾 Guardar cambios en tarea"):
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE tareas
                    SET descripcion = :desc, responsable = :resp, estado = :estado
                    WHERE descripcion = :original
                """), {"desc": nuevo_desc, "resp": nuevo_resp_tarea, "estado": nuevo_estado_tarea, "original": tarea_editar})
            st.success("Tarea actualizada correctamente")
            st.rerun()
    if not proyectos.empty:
        editar_id = st.selectbox("Proyecto a editar/eliminar", proyectos['nombre'])
        if st.button("🗑 Eliminar Proyecto"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM tareas WHERE proyecto_id = (SELECT id FROM proyectos WHERE nombre = :nombre)"), {"nombre": editar_id})
                conn.execute(text("DELETE FROM proyectos WHERE nombre = :nombre"), {"nombre": editar_id})
            st.success("Proyecto y tareas eliminados")
            st.rerun()
    if not procesos.empty:
        eliminar_proc = st.selectbox("Proceso a eliminar", procesos['nombre'])
        if st.button("🗑 Eliminar Proceso"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM subprocesos WHERE proceso_id = (SELECT id FROM procesos WHERE nombre = :nombre)"), {"nombre": eliminar_proc})
                conn.execute(text("DELETE FROM procesos WHERE nombre = :nombre"), {"nombre": eliminar_proc})
            st.success("Proceso y subprocesos eliminados")
            st.rerun()
    if not tareas.empty:
        eliminar_tarea = st.selectbox("Tarea a eliminar", tareas['descripcion'])
        if st.button("🗑 Eliminar Tarea"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM tareas WHERE descripcion = :desc"), {"desc": eliminar_tarea})
            st.success("Tarea eliminada")
            st.experimental_rerun()
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
        proyecto_id = proyectos.loc[proyectos['nombre'] == proyecto_sel, 'proyecto_id'].values[0]
        tarea_existente = pd.read_sql("SELECT * FROM tareas WHERE proyecto_id = :pid AND descripcion = :desc", engine, params={"pid": proyecto_id, "desc": descripcion})
        if not tarea_existente.empty:
            st.warning("⚠️ Ya existe una tarea con esa descripción en este proyecto.")
        else:
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
            st.experimental_rerun()



if tareas.empty:
    st.warning("⚠️ No hay tareas registradas. Comienza agregando tareas desde la barra lateral.")
    st.stop()

# Filtros
st.sidebar.header("🔍 Filtros")
fecha_inicio = st.sidebar.date_input("Desde", value=pd.to_datetime("2024-01-01"))
fecha_fin = st.sidebar.date_input("Hasta", value=pd.to_datetime("today"))
responsables = ['Todos'] + sorted(tareas['responsable'].dropna().unique().tolist()) if not tareas.empty else ['Todos']
filtro_resp = st.sidebar.selectbox("Responsable", responsables)

# Filtrar tareas por fechas y responsable
filtradas = tareas.copy()
filtradas['fecha_inicio'] = pd.to_datetime(filtradas['fecha_inicio'], errors='coerce')
filtradas['fecha_fin'] = pd.to_datetime(filtradas['fecha_fin'], errors='coerce')
filtradas = filtradas[(filtradas['fecha_inicio'] >= pd.to_datetime(fecha_inicio)) &
                      (filtradas['fecha_inicio'] <= pd.to_datetime(fecha_fin))]
if filtro_resp != 'Todos':
    filtradas = filtradas[filtradas['responsable'] == filtro_resp]

if filtradas.empty:
    st.info("⚠️ No hay tareas que cumplan con los filtros seleccionados.")
    st.stop()

# Semaforización y avance por proyecto
avance = filtradas.groupby(['proyecto_id', 'estado']).size().unstack(fill_value=0).reset_index()
proyectos = proyectos.rename(columns={'id': 'proyecto_id'})
avance = avance.merge(proyectos, on='proyecto_id', how='left')
for col in ['Pendiente', 'En curso', 'Finalizada']:
    if col not in avance.columns:
        avance[col] = 0
avance['Total'] = avance[['Pendiente', 'En curso', 'Finalizada']].sum(axis=1)
avance['% Avance'] = (avance['Finalizada'] / avance['Total'] * 100).round(1)

st.subheader("📌 Porcentaje de Avance y Estado de Proyectos")
st.dataframe(avance[['nombre', 'responsable', 'Pendiente', 'En curso', 'Finalizada', '% Avance']])

# Diagrama de Gantt
if filtradas.empty:
    st.info("⚠️ No hay tareas disponibles en el rango de fechas o filtros aplicados.")
else:
    st.subheader("🗓️ Diagrama de Gantt")
    filtradas['descripcion'] = filtradas['descripcion'].fillna('')
    fig_gantt = px.timeline(filtradas, x_start='fecha_inicio', x_end='fecha_fin',
                            y='descripcion', color='estado', title='Gantt de Tareas')
    fig_gantt.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_gantt, use_container_width=True)

# Gráfico de avance por responsable
if not filtradas.empty:
    st.subheader("👤 Tareas por Responsable")
    estado_resp = filtradas.groupby(['responsable', 'estado']).size().reset_index(name='cantidad')
    fig_estado = px.bar(estado_resp, x='responsable', y='cantidad', color='estado', barmode='group')
    st.plotly_chart(fig_estado, use_container_width=True)

# Exportación
st.download_button("📥 Exportar resumen a CSV", data=avance.to_csv(index=False).encode('utf-8'),
                   file_name="resumen_avance.csv", mime="text/csv")
