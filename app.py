# Dashboard de Seguimiento de Proyectos por Procesos y Subprocesos

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(page_title="Gestor de Proyectos", layout="wide")
st.title("📊 Dashboard de Seguimiento de Proyectos")

engine = create_engine("sqlite:///seguimiento.db")

# Crear tablas con estructura corregida
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
        fecha_creacion TEXT,
        FOREIGN KEY (proceso_id) REFERENCES procesos(id)
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
        fecha_finalizacion TEXT,
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
        fecha_creacion TEXT,
        fecha_proyeccion TEXT,
        fecha_cumplimiento TEXT,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id)
    );
    """))

@st.cache_data
def cargar_datos():
    procesos = pd.read_sql("SELECT * FROM procesos", engine)
    subprocesos = pd.read_sql("SELECT * FROM subprocesos", engine)
    proyectos = pd.read_sql("SELECT * FROM proyectos", engine)
    tareas = pd.read_sql("SELECT * FROM tareas", engine)
    return procesos, subprocesos, proyectos, tareas

# Función para limpiar cache y recargar datos
def actualizar_datos():
    st.cache_data.clear()
    return cargar_datos()

procesos, subprocesos, proyectos, tareas = cargar_datos()

st.sidebar.header("🧩 Gestión Jerárquica")

# PROCESOS
st.sidebar.subheader("Procesos")
nuevo_proc = st.sidebar.text_input("Nuevo Proceso")
if st.sidebar.button("Crear Proceso") and nuevo_proc.strip():
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO procesos (nombre, fecha_creacion) VALUES (:n, :f)"), 
                    {"n": nuevo_proc.strip(), "f": datetime.now().isoformat()})
    procesos, subprocesos, proyectos, tareas = actualizar_datos()
    st.rerun()

# Lista de procesos disponibles
opciones_procesos = [""] + procesos['nombre'].tolist() if not procesos.empty else [""]
proc_sel = st.sidebar.selectbox("Seleccionar Proceso", opciones_procesos, key="proceso_select")

if st.sidebar.button("Eliminar Proceso") and proc_sel:
    with engine.begin() as conn:
        pid = procesos[procesos['nombre'] == proc_sel]['id'].values[0]
        # Eliminar en cascada
        conn.execute(text("DELETE FROM tareas WHERE proyecto_id IN (SELECT id FROM proyectos WHERE proceso_id = :pid)"), {"pid": pid})
        conn.execute(text("DELETE FROM proyectos WHERE proceso_id = :pid"), {"pid": pid})
        conn.execute(text("DELETE FROM subprocesos WHERE proceso_id = :pid"), {"pid": pid})
        conn.execute(text("DELETE FROM procesos WHERE id = :pid"), {"pid": pid})
    procesos, subprocesos, proyectos, tareas = actualizar_datos()
    st.rerun()

# SUBPROCESOS
st.sidebar.subheader("Subprocesos")
subproc_df = pd.DataFrame()
proc_id = None

if proc_sel:
    proc_id = procesos[procesos['nombre'] == proc_sel]['id'].values[0]
   subproc_df = subprocesos[subprocesos['subproceso_id'] == proc_id]

nuevo_subproc = st.sidebar.text_input("Nuevo Subproceso")
if st.sidebar.button("Crear Subproceso") and nuevo_subproc.strip() and proc_sel:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id, fecha_creacion) VALUES (:n, :pid, :f)"), 
                    {"n": nuevo_subproc.strip(), "pid": proc_id, "f": datetime.now().isoformat()})
    procesos, subprocesos, proyectos, tareas = actualizar_datos()
    st.rerun()

# Lista de subprocesos disponibles
opciones_subprocesos = [""] + subproc_df['nombre'].tolist() if not subproc_df.empty else [""]
subproc_sel = st.sidebar.selectbox("Seleccionar Subproceso", opciones_subprocesos, key="subproceso_select")

if st.sidebar.button("Eliminar Subproceso") and subproc_sel:
    spid = subproc_df[subproc_df['nombre'] == subproc_sel]['id'].values[0]
    with engine.begin() as conn:
        # Eliminar en cascada
        conn.execute(text("DELETE FROM tareas WHERE proyecto_id IN (SELECT id FROM proyectos WHERE subproceso_id = :spid)"), {"spid": spid})
        conn.execute(text("DELETE FROM proyectos WHERE subproceso_id = :spid"), {"spid": spid})
        conn.execute(text("DELETE FROM subprocesos WHERE id = :spid"), {"spid": spid})
    procesos, subprocesos, proyectos, tareas = actualizar_datos()
    st.rerun()

# PROYECTOS
st.sidebar.subheader("Proyectos")
nombre_proy = st.sidebar.text_input("Nombre Proyecto")
responsable_proy = st.sidebar.text_input("Responsable Principal")
fecha_proy = st.sidebar.date_input("Fecha Proyectada")

if st.sidebar.button("Crear Proyecto") and nombre_proy.strip() and proc_sel and subproc_sel:
    spid = subproc_df[subproc_df['nombre'] == subproc_sel]['id'].values[0]
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO proyectos (nombre, responsable, estado, proceso_id, subproceso_id, fecha_creacion, fecha_proyeccion)
            VALUES (:n, :r, 'Pendiente', :pid, :spid, :f, :p)"""),
            {"n": nombre_proy.strip(), "r": responsable_proy.strip(), "pid": proc_id, "spid": spid, 
             "f": datetime.now().isoformat(), "p": fecha_proy.isoformat()})
    procesos, subprocesos, proyectos, tareas = actualizar_datos()
    st.rerun()

# Lista de proyectos disponibles
proy_df = pd.DataFrame()
if subproc_sel and not subproc_df.empty:
    spid = subproc_df[subproc_df['nombre'] == subproc_sel]['id'].values[0]
    proy_df = proyectos[proyectos['subproceso_id'] == spid]

opciones_proyectos = [""] + proy_df['nombre'].tolist() if not proy_df.empty else [""]
proy_sel = st.sidebar.selectbox("Seleccionar Proyecto", opciones_proyectos, key="proyecto_select")

if st.sidebar.button("Eliminar Proyecto") and proy_sel:
    prid = proy_df[proy_df['nombre'] == proy_sel]['id'].values[0]
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM tareas WHERE proyecto_id = :prid"), {"prid": prid})
        conn.execute(text("DELETE FROM proyectos WHERE id = :prid"), {"prid": prid})
    procesos, subprocesos, proyectos, tareas = actualizar_datos()
    st.rerun()

# TAREAS
st.sidebar.subheader("Tareas")
desc = st.sidebar.text_area("Descripción")
resp = st.sidebar.text_input("Responsable")
fini = st.sidebar.date_input("Inicio")
ffin = st.sidebar.date_input("Fin")
fproy = st.sidebar.date_input("Fecha Proyección")

if st.sidebar.button("Crear Tarea") and proy_sel and desc.strip():
    prid = proy_df[proy_df['nombre'] == proy_sel]['id'].values[0]
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO tareas (proyecto_id, descripcion, responsable, fecha_inicio, fecha_fin, estado, fecha_creacion, fecha_proyeccion)
            VALUES (:pid, :d, :r, :i, :f, 'Pendiente', :fc, :fp)"""),
            {"pid": prid, "d": desc.strip(), "r": resp.strip(), "i": fini.isoformat(), "f": ffin.isoformat(), 
             "fc": datetime.now().isoformat(), "fp": fproy.isoformat()})
    procesos, subprocesos, proyectos, tareas = actualizar_datos()
    st.rerun()

# VISUALIZACIÓN
st.header("📌 Seguimiento Visual")

# Mostrar información de contexto
if proc_sel:
    st.info(f"📋 **Proceso:** {proc_sel}")
    if subproc_sel:
        st.info(f"🔹 **Subproceso:** {subproc_sel}")
        if proy_sel:
            st.info(f"🎯 **Proyecto:** {proy_sel}")

# Filtrar tareas del proyecto seleccionado
tareas_filtradas = pd.DataFrame()
if proy_sel and not proy_df.empty:
    prid = proy_df[proy_df['nombre'] == proy_sel]['id'].values[0]
    tareas_filtradas = tareas[tareas['proyecto_id'] == prid]

if tareas_filtradas.empty:
    if proy_sel:
        st.info("No hay tareas disponibles para este proyecto.")
    else:
        st.info("Selecciona un proyecto para ver sus tareas.")
else:
    # Gráfico de Gantt
    tareas_filtradas = tareas_filtradas.copy()
    tareas_filtradas['fecha_inicio'] = pd.to_datetime(tareas_filtradas['fecha_inicio'])
    tareas_filtradas['fecha_fin'] = pd.to_datetime(tareas_filtradas['fecha_fin'])
    
    gantt = px.timeline(tareas_filtradas, x_start='fecha_inicio', x_end='fecha_fin', 
                       y='descripcion', color='estado', title="Cronograma de Tareas")
    gantt.update_yaxes(autorange='reversed')
    st.plotly_chart(gantt, use_container_width=True)

    # Gráfico de desviaciones
    tareas_filtradas['fecha_proyeccion'] = pd.to_datetime(tareas_filtradas['fecha_proyeccion'])
    tareas_filtradas['desviacion'] = (tareas_filtradas['fecha_fin'] - tareas_filtradas['fecha_proyeccion']).dt.days

    dev = px.bar(tareas_filtradas, x='descripcion', y='desviacion', color='estado',
                title="Desviaciones respecto a la fecha proyectada (días)")
    st.plotly_chart(dev, use_container_width=True)

    # Tabla de tareas
    st.subheader("Lista de Tareas")
    st.dataframe(tareas_filtradas[['descripcion', 'responsable', 'fecha_inicio', 'fecha_fin', 'estado']])

    # Actualizar estado de tareas
    if not tareas_filtradas.empty:
        st.subheader("Actualizar Estado de Tareas")
        tarea_para_actualizar = st.selectbox("Seleccionar Tarea", 
                                           [""] + tareas_filtradas['descripcion'].tolist())
        nuevo_estado = st.selectbox("Nuevo Estado", ["Pendiente", "En curso", "Finalizada"])
        
        if st.button("Actualizar Estado") and tarea_para_actualizar:
            tid = tareas_filtradas[tareas_filtradas['descripcion'] == tarea_para_actualizar]['id'].values[0]
            with engine.begin() as conn:
                fecha_cumplimiento = datetime.now().isoformat() if nuevo_estado == "Finalizada" else None
                conn.execute(text("UPDATE tareas SET estado = :estado, fecha_cumplimiento = :fc WHERE id = :id"),
                           {"estado": nuevo_estado, "fc": fecha_cumplimiento, "id": tid})
            st.success(f"Estado actualizado a: {nuevo_estado}")
            procesos, subprocesos, proyectos, tareas = actualizar_datos()
            st.rerun()

# Resumen general de proyectos
if not proyectos.empty:
    st.header("📊 Resumen General")
    
    # Crear resumen con información de tareas
    resumen_data = []
    for _, proyecto in proyectos.iterrows():
        tareas_proyecto = tareas[tareas['proyecto_id'] == proyecto['id']]
        pendientes = len(tareas_proyecto[tareas_proyecto['estado'] == 'Pendiente'])
        en_curso = len(tareas_proyecto[tareas_proyecto['estado'] == 'En curso'])
        finalizadas = len(tareas_proyecto[tareas_proyecto['estado'] == 'Finalizada'])
        total = pendientes + en_curso + finalizadas
        avance = (finalizadas / total * 100) if total > 0 else 0
        
        resumen_data.append({
            'Proyecto': proyecto['nombre'],
            'Responsable': proyecto['responsable'],
            'Estado': proyecto['estado'],
            'Pendientes': pendientes,
            'En Curso': en_curso,
            'Finalizadas': finalizadas,
            'Total Tareas': total,
            'Avance %': round(avance, 1)
        })
    
    if resumen_data:
        resumen_df = pd.DataFrame(resumen_data)
        st.dataframe(resumen_df, use_container_width=True)

# Finalizar proyecto
if proy_sel and not proy_df.empty:
    st.subheader("🏁 Finalizar Proyecto")
    if st.button("✅ Finalizar Proyecto Seleccionado"):
        prid = proy_df[proy_df['nombre'] == proy_sel]['id'].values[0]
        with engine.begin() as conn:
            conn.execute(text("UPDATE proyectos SET estado = 'Finalizado', fecha_finalizacion = :f WHERE id = :id"),
                         {"f": datetime.now().isoformat(), "id": prid})
        st.success(f"Proyecto '{proy_sel}' finalizado exitosamente!")
        procesos, subprocesos, proyectos, tareas = actualizar_datos()
        st.rerun()
