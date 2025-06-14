# Dashboard de Seguimiento de Proyectos por Procesos y Subprocesos - VERSIÓN CORREGIDA

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(page_title="Gestor de Proyectos", layout="wide")
st.title("📊 Dashboard de Seguimiento de Proyectos")

# Inicializar la base de datos
@st.cache_resource
def init_database():
    engine = create_engine("sqlite:///seguimiento.db")
    
    # Crear tablas con estructura corregida
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS procesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            fecha_creacion TEXT
        );
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS subprocesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            proceso_id INTEGER,
            fecha_creacion TEXT,
            FOREIGN KEY (proceso_id) REFERENCES procesos(id) ON DELETE CASCADE
        );
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            responsable TEXT,
            estado TEXT DEFAULT 'Pendiente',
            proceso_id INTEGER,
            subproceso_id INTEGER,
            fecha_creacion TEXT,
            fecha_proyeccion TEXT,
            fecha_finalizacion TEXT,
            FOREIGN KEY (proceso_id) REFERENCES procesos(id) ON DELETE CASCADE,
            FOREIGN KEY (subproceso_id) REFERENCES subprocesos(id) ON DELETE CASCADE
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
            estado TEXT DEFAULT 'Pendiente',
            fecha_creacion TEXT,
            fecha_proyeccion TEXT,
            fecha_cumplimiento TEXT,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        );
        """))
    
    return engine

engine = init_database()

# Función para cargar datos desde la base de datos
def cargar_datos():
    try:
        procesos = pd.read_sql("SELECT * FROM procesos ORDER BY fecha_creacion DESC", engine)
        subprocesos = pd.read_sql("SELECT * FROM subprocesos ORDER BY fecha_creacion DESC", engine)
        proyectos = pd.read_sql("SELECT * FROM proyectos ORDER BY fecha_creacion DESC", engine)
        tareas = pd.read_sql("SELECT * FROM tareas ORDER BY fecha_creacion DESC", engine)
        return procesos, subprocesos, proyectos, tareas
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Función para actualizar datos y limpiar cache
def actualizar_datos():
    st.cache_data.clear()
    return cargar_datos()

# Inicializar estado de sesión
if 'proceso_seleccionado' not in st.session_state:
    st.session_state.proceso_seleccionado = ""
if 'subproceso_seleccionado' not in st.session_state:
    st.session_state.subproceso_seleccionado = ""
if 'proyecto_seleccionado' not in st.session_state:
    st.session_state.proyecto_seleccionado = ""

# Cargar datos
procesos, subprocesos, proyectos, tareas = cargar_datos()

# Sidebar para gestión jerárquica
st.sidebar.header("🧩 Gestión Jerárquica")

# ============= GESTIÓN DE PROCESOS =============
st.sidebar.subheader("1️⃣ Procesos")

# Mostrar procesos existentes
if not procesos.empty:
    st.sidebar.write("**Procesos existentes:**")
    for _, proceso in procesos.iterrows():
        st.sidebar.write(f"• {proceso['nombre']}")

# Crear nuevo proceso
with st.sidebar.expander("➕ Crear Nuevo Proceso"):
    nuevo_proceso = st.text_input("Nombre del Proceso", key="nuevo_proceso")
    if st.button("Crear Proceso", key="btn_crear_proceso"):
        if nuevo_proceso.strip():
            try:
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO procesos (nombre, fecha_creacion) VALUES (:n, :f)"), 
                                {"n": nuevo_proceso.strip(), "f": datetime.now().isoformat()})
                st.success(f"✅ Proceso '{nuevo_proceso}' creado exitosamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al crear proceso: {e}")
        else:
            st.warning("⚠️ Ingrese un nombre válido para el proceso")

# Seleccionar proceso
opciones_procesos = ["Seleccionar proceso..."] + (procesos['nombre'].tolist() if not procesos.empty else [])
proceso_seleccionado = st.sidebar.selectbox(
    "Seleccionar Proceso", 
    opciones_procesos, 
    key="select_proceso",
    index=0
)

# Actualizar estado de sesión
if proceso_seleccionado != "Seleccionar proceso...":
    st.session_state.proceso_seleccionado = proceso_seleccionado
else:
    st.session_state.proceso_seleccionado = ""

# Eliminar proceso
if st.session_state.proceso_seleccionado:
    with st.sidebar.expander("🗑️ Eliminar Proceso"):
        st.warning(f"¿Eliminar '{st.session_state.proceso_seleccionado}'?")
        st.write("⚠️ Esto eliminará todos los subprocesos, proyectos y tareas asociados")
        if st.button("Confirmar Eliminación", key="btn_eliminar_proceso"):
            try:
                with engine.begin() as conn:
                    pid = procesos[procesos['nombre'] == st.session_state.proceso_seleccionado]['id'].values[0]
                    conn.execute(text("DELETE FROM procesos WHERE id = :pid"), {"pid": pid})
                st.success(f"✅ Proceso '{st.session_state.proceso_seleccionado}' eliminado")
                st.session_state.proceso_seleccionado = ""
                st.session_state.subproceso_seleccionado = ""
                st.session_state.proyecto_seleccionado = ""
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al eliminar proceso: {e}")

# ============= GESTIÓN DE SUBPROCESOS =============
st.sidebar.subheader("2️⃣ Subprocesos")

if st.session_state.proceso_seleccionado:
    st.sidebar.info(f"📋 Proceso: {st.session_state.proceso_seleccionado}")
    
    # Obtener subprocesos del proceso seleccionado
    proc_id = procesos[procesos['nombre'] == st.session_state.proceso_seleccionado]['id'].values[0]
    subproc_df = subprocesos[subprocesos['proceso_id'] == proc_id]
    
    # Mostrar subprocesos existentes
    if not subproc_df.empty:
        st.sidebar.write("**Subprocesos existentes:**")
        for _, subproceso in subproc_df.iterrows():
            st.sidebar.write(f"• {subproceso['nombre']}")
    
    # Crear nuevo subproceso
    with st.sidebar.expander("➕ Crear Nuevo Subproceso"):
        nuevo_subproceso = st.text_input("Nombre del Subproceso", key="nuevo_subproceso")
        if st.button("Crear Subproceso", key="btn_crear_subproceso"):
            if nuevo_subproceso.strip():
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id, fecha_creacion) VALUES (:n, :pid, :f)"), 
                                    {"n": nuevo_subproceso.strip(), "pid": proc_id, "f": datetime.now().isoformat()})
                    st.success(f"✅ Subproceso '{nuevo_subproceso}' creado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al crear subproceso: {e}")
            else:
                st.warning("⚠️ Ingrese un nombre válido para el subproceso")
    
    # Seleccionar subproceso
    opciones_subprocesos = ["Seleccionar subproceso..."] + (subproc_df['nombre'].tolist() if not subproc_df.empty else [])
    subproceso_seleccionado = st.sidebar.selectbox(
        "Seleccionar Subproceso", 
        opciones_subprocesos, 
        key="select_subproceso",
        index=0
    )
    
    # Actualizar estado de sesión
    if subproceso_seleccionado != "Seleccionar subproceso...":
        st.session_state.subproceso_seleccionado = subproceso_seleccionado
    else:
        st.session_state.subproceso_seleccionado = ""
    
    # Eliminar subproceso
    if st.session_state.subproceso_seleccionado:
        with st.sidebar.expander("🗑️ Eliminar Subproceso"):
            st.warning(f"¿Eliminar '{st.session_state.subproceso_seleccionado}'?")
            st.write("⚠️ Esto eliminará todos los proyectos y tareas asociados")
            if st.button("Confirmar Eliminación", key="btn_eliminar_subproceso"):
                try:
                    with engine.begin() as conn:
                        spid = subproc_df[subproc_df['nombre'] == st.session_state.subproceso_seleccionado]['id'].values[0]
                        conn.execute(text("DELETE FROM subprocesos WHERE id = :spid"), {"spid": spid})
                    st.success(f"✅ Subproceso '{st.session_state.subproceso_seleccionado}' eliminado")
                    st.session_state.subproceso_seleccionado = ""
                    st.session_state.proyecto_seleccionado = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al eliminar subproceso: {e}")

else:
    st.sidebar.info("ℹ️ Seleccione un proceso para gestionar subprocesos")

# ============= GESTIÓN DE PROYECTOS =============
st.sidebar.subheader("3️⃣ Proyectos")

if st.session_state.proceso_seleccionado and st.session_state.subproceso_seleccionado:
    st.sidebar.info(f"📋 Proceso: {st.session_state.proceso_seleccionado}")
    st.sidebar.info(f"🔹 Subproceso: {st.session_state.subproceso_seleccionado}")
    
    # Obtener proyectos del subproceso seleccionado
    spid = subproc_df[subproc_df['nombre'] == st.session_state.subproceso_seleccionado]['id'].values[0]
    proy_df = proyectos[proyectos['subproceso_id'] == spid]
    
    # Mostrar proyectos existentes
    if not proy_df.empty:
        st.sidebar.write("**Proyectos existentes:**")
        for _, proyecto in proy_df.iterrows():
            st.sidebar.write(f"• {proyecto['nombre']} ({proyecto['estado']})")
    
    # Crear nuevo proyecto
    with st.sidebar.expander("➕ Crear Nuevo Proyecto"):
        nombre_proyecto = st.text_input("Nombre del Proyecto", key="nuevo_proyecto")
        responsable_proyecto = st.text_input("Responsable Principal", key="responsable_proyecto")
        fecha_proyeccion = st.date_input("Fecha Proyectada", key="fecha_proyeccion")
        
        if st.button("Crear Proyecto", key="btn_crear_proyecto"):
            if nombre_proyecto.strip():
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO proyectos (nombre, responsable, estado, proceso_id, subproceso_id, fecha_creacion, fecha_proyeccion)
                            VALUES (:n, :r, 'Pendiente', :pid, :spid, :f, :p)"""),
                            {"n": nombre_proyecto.strip(), "r": responsable_proyecto.strip(), 
                             "pid": proc_id, "spid": spid, 
                             "f": datetime.now().isoformat(), "p": fecha_proyeccion.isoformat()})
                    st.success(f"✅ Proyecto '{nombre_proyecto}' creado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al crear proyecto: {e}")
            else:
                st.warning("⚠️ Ingrese un nombre válido para el proyecto")
    
    # Seleccionar proyecto
    opciones_proyectos = ["Seleccionar proyecto..."] + (proy_df['nombre'].tolist() if not proy_df.empty else [])
    proyecto_seleccionado = st.sidebar.selectbox(
        "Seleccionar Proyecto", 
        opciones_proyectos, 
        key="select_proyecto",
        index=0
    )
    
    # Actualizar estado de sesión
    if proyecto_seleccionado != "Seleccionar proyecto...":
        st.session_state.proyecto_seleccionado = proyecto_seleccionado
    else:
        st.session_state.proyecto_seleccionado = ""
    
    # Eliminar proyecto
    if st.session_state.proyecto_seleccionado:
        with st.sidebar.expander("🗑️ Eliminar Proyecto"):
            st.warning(f"¿Eliminar '{st.session_state.proyecto_seleccionado}'?")
            st.write("⚠️ Esto eliminará todas las tareas asociadas")
            if st.button("Confirmar Eliminación", key="btn_eliminar_proyecto"):
                try:
                    with engine.begin() as conn:
                        prid = proy_df[proy_df['nombre'] == st.session_state.proyecto_seleccionado]['id'].values[0]
                        conn.execute(text("DELETE FROM proyectos WHERE id = :prid"), {"prid": prid})
                    st.success(f"✅ Proyecto '{st.session_state.proyecto_seleccionado}' eliminado")
                    st.session_state.proyecto_seleccionado = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al eliminar proyecto: {e}")

else:
    st.sidebar.info("ℹ️ Seleccione un proceso y subproceso para gestionar proyectos")

# ============= GESTIÓN DE TAREAS =============
st.sidebar.subheader("4️⃣ Tareas")

if st.session_state.proyecto_seleccionado:
    st.sidebar.info(f"🎯 Proyecto: {st.session_state.proyecto_seleccionado}")
    
    # Crear nueva tarea
    with st.sidebar.expander("➕ Crear Nueva Tarea"):
        descripcion_tarea = st.text_area("Descripción de la Tarea", key="descripcion_tarea")
        responsable_tarea = st.text_input("Responsable", key="responsable_tarea")
        fecha_inicio = st.date_input("Fecha de Inicio", key="fecha_inicio")
        fecha_fin = st.date_input("Fecha de Fin", key="fecha_fin")
        fecha_proyeccion_tarea = st.date_input("Fecha Proyección", key="fecha_proyeccion_tarea")
        
        if st.button("Crear Tarea", key="btn_crear_tarea"):
            if descripcion_tarea.strip():
                try:
                    prid = proy_df[proy_df['nombre'] == st.session_state.proyecto_seleccionado]['id'].values[0]
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO tareas (proyecto_id, descripcion, responsable, fecha_inicio, fecha_fin, estado, fecha_creacion, fecha_proyeccion)
                            VALUES (:pid, :d, :r, :i, :f, 'Pendiente', :fc, :fp)"""),
                            {"pid": prid, "d": descripcion_tarea.strip(), "r": responsable_tarea.strip(), 
                             "i": fecha_inicio.isoformat(), "f": fecha_fin.isoformat(), 
                             "fc": datetime.now().isoformat(), "fp": fecha_proyeccion_tarea.isoformat()})
                    st.success("✅ Tarea creada exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al crear tarea: {e}")
            else:
                st.warning("⚠️ Ingrese una descripción válida para la tarea")
else:
    st.sidebar.info("ℹ️ Seleccione un proyecto para gestionar tareas")

# ============= ÁREA PRINCIPAL - VISUALIZACIÓN =============
st.header("📌 Seguimiento Visual")

# Mostrar información de contexto
if st.session_state.proceso_seleccionado:
    st.success(f"📋 **Proceso:** {st.session_state.proceso_seleccionado}")
    if st.session_state.subproceso_seleccionado:
        st.success(f"🔹 **Subproceso:** {st.session_state.subproceso_seleccionado}")
        if st.session_state.proyecto_seleccionado:
            st.success(f"🎯 **Proyecto:** {st.session_state.proyecto_seleccionado}")

# Filtrar y mostrar tareas del proyecto seleccionado
if st.session_state.proyecto_seleccionado:
    prid = proy_df[proy_df['nombre'] == st.session_state.proyecto_seleccionado]['id'].values[0]
    tareas_filtradas = tareas[tareas['proyecto_id'] == prid].copy()
    
    if not tareas_filtradas.empty:
        # Gráfico de Gantt
        st.subheader("📅 Cronograma de Tareas")
        tareas_filtradas['fecha_inicio'] = pd.to_datetime(tareas_filtradas['fecha_inicio'])
        tareas_filtradas['fecha_fin'] = pd.to_datetime(tareas_filtradas['fecha_fin'])
        
        gantt = px.timeline(
            tareas_filtradas, 
            x_start='fecha_inicio', 
            x_end='fecha_fin', 
            y='descripcion', 
            color='estado', 
            title="Cronograma de Tareas",
            color_discrete_map={
                'Pendiente': '#ff7f7f',
                'En curso': '#ffb347', 
                'Finalizada': '#77dd77'
            }
        )
        gantt.update_yaxes(autorange='reversed')
        gantt.update_layout(height=400)
        st.plotly_chart(gantt, use_container_width=True)

        # Gráfico de desviaciones
        st.subheader("📊 Análisis de Desviaciones")
        tareas_filtradas['fecha_proyeccion'] = pd.to_datetime(tareas_filtradas['fecha_proyeccion'])
        tareas_filtradas['desviacion'] = (tareas_filtradas['fecha_fin'] - tareas_filtradas['fecha_proyeccion']).dt.days

        dev = px.bar(
            tareas_filtradas, 
            x='descripcion', 
            y='desviacion', 
            color='estado',
            title="Desviaciones respecto a la fecha proyectada (días)",
            color_discrete_map={
                'Pendiente': '#ff7f7f',
                'En curso': '#ffb347', 
                'Finalizada': '#77dd77'
            }
        )
        dev.update_layout(height=400)
        st.plotly_chart(dev, use_container_width=True)

        # Tabla de tareas
        st.subheader("📋 Lista de Tareas")
        tareas_display = tareas_filtradas[['descripcion', 'responsable', 'fecha_inicio', 'fecha_fin', 'estado']].copy()
        tareas_display.columns = ['Descripción', 'Responsable', 'Fecha Inicio', 'Fecha Fin', 'Estado']
        st.dataframe(tareas_display, use_container_width=True)

        # Actualizar estado de tareas
        st.subheader("✏️ Actualizar Estado de Tareas")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            tarea_para_actualizar = st.selectbox(
                "Seleccionar Tarea", 
                ["Seleccionar tarea..."] + tareas_filtradas['descripcion'].tolist(),
                key="tarea_actualizar"
            )
        
        with col2:
            nuevo_estado = st.selectbox(
                "Nuevo Estado", 
                ["Pendiente", "En curso", "Finalizada"],
                key="nuevo_estado"
            )
        
        with col3:
            if st.button("Actualizar Estado", key="btn_actualizar_estado"):
                if tarea_para_actualizar != "Seleccionar tarea...":
                    try:
                        tid = tareas_filtradas[tareas_filtradas['descripcion'] == tarea_para_actualizar]['id'].values[0]
                        with engine.begin() as conn:
                            fecha_cumplimiento = datetime.now().isoformat() if nuevo_estado == "Finalizada" else None
                            conn.execute(text("UPDATE tareas SET estado = :estado, fecha_cumplimiento = :fc WHERE id = :id"),
                                       {"estado": nuevo_estado, "fc": fecha_cumplimiento, "id": tid})
                        st.success(f"✅ Estado actualizado a: {nuevo_estado}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al actualizar estado: {e}")
                else:
                    st.warning("⚠️ Seleccione una tarea para actualizar")
    else:
        st.info("ℹ️ No hay tareas disponibles para este proyecto.")
else:
    st.info("ℹ️ Seleccione un proyecto para ver sus tareas y gráficos.")

# ============= RESUMEN GENERAL =============
st.header("📊 Resumen General")

if not proyectos.empty:
    # Crear resumen con información de tareas
    resumen_data = []
    for _, proyecto in proyectos.iterrows():
        tareas_proyecto = tareas[tareas['proyecto_id'] == proyecto['id']]
        pendientes = len(tareas_proyecto[tareas_proyecto['estado'] == 'Pendiente'])
        en_curso = len(tareas_proyecto[tareas_proyecto['estado'] == 'En curso'])
        finalizadas = len(tareas_proyecto[tareas_proyecto['estado'] == 'Finalizada'])
        total = pendientes + en_curso + finalizadas
        avance = (finalizadas / total * 100) if total > 0 else 0
        
        # Obtener nombres de proceso y subproceso
        proceso_nombre = procesos[procesos['id'] == proyecto['proceso_id']]['nombre'].values[0] if not procesos.empty else "N/A"
        subproceso_nombre = subprocesos[subprocesos['id'] == proyecto['subproceso_id']]['nombre'].values[0] if not subprocesos.empty else "N/A"
        
        resumen_data.append({
            'Proceso': proceso_nombre,
            'Subproceso': subproceso_nombre,
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
        
        # Gráfico de avance por proyecto
        if len(resumen_df) > 0:
            fig_avance = px.bar(
                resumen_df, 
                x='Proyecto', 
                y='Avance %', 
                color='Estado',
                title="Avance por Proyecto (%)",
                color_discrete_map={
                    'Pendiente': '#ff7f7f',
                    'En curso': '#ffb347', 
                    'Finalizado': '#77dd77'
                }
            )
            fig_avance.update_layout(height=400)
            st.plotly_chart(fig_avance, use_container_width=True)
else:
    st.info("ℹ️ No hay proyectos disponibles.")

# ============= FINALIZAR PROYECTO =============
if st.session_state.proyecto_seleccionado:
    st.header("🏁 Finalizar Proyecto")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info(f"Proyecto seleccionado: **{st.session_state.proyecto_seleccionado}**")
    
    with col2:
        if st.button("✅ Finalizar Proyecto Seleccionado", key="btn_finalizar_proyecto"):
            try:
                prid = proy_df[proy_df['nombre'] == st.session_state.proyecto_seleccionado]['id'].values[0]
                with engine.begin() as conn:
                    conn.execute(text("UPDATE proyectos SET estado = 'Finalizado', fecha_finalizacion = :f WHERE id = :id"),
                                 {"f": datetime.now().isoformat(), "id": prid})
                st.success(f"🎉 Proyecto '{st.session_state.proyecto_seleccionado}' finalizado exitosamente!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al finalizar proyecto: {e}")

# ============= ESTADÍSTICAS ADICIONALES =============
st.header("📈 Estadísticas Adicionales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Procesos", len(procesos))

with col2:
    st.metric("Total Subprocesos", len(subprocesos))

with col3:
    st.metric("Total Proyectos", len(proyectos))

with col4:
    st.metric("Total Tareas", len(tareas))

# Información de ayuda
with st.expander("ℹ️ Información de Ayuda"):
    st.markdown("""
    ### Cómo usar este dashboard:
    
    1. **Crear Proceso**: Comience creando un proceso en la barra lateral
    2. **Crear Subproceso**: Seleccione un proceso y luego cree subprocesos
    3. **Crear Proyecto**: Seleccione un subproceso y cree proyectos
    4. **Crear Tareas**: Seleccione un proyecto y agregue tareas
    5. **Seguimiento**: Use los gráficos y tablas para monitorear el progreso
    
    ### Funcionalidades principales:
    - ✅ Gestión jerárquica de procesos, subprocesos, proyectos y tareas
    - 📊 Visualización con gráficos de Gantt y análisis de desviaciones
    - 📈 Seguimiento de avance y estadísticas en tiempo real
    - 🗑️ Eliminación segura con confirmación
    - 💾 Persistencia de datos en base de datos SQLite
    """)
