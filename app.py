
# (código anterior conservado...)

# --- Formulario de ingreso de contratos ---
st.subheader("📑 Registrar nuevo contrato")
with st.form("form_contrato"):
    nombre_contrato = st.text_input("Nombre del contrato")
    fecha_inicio_contrato = st.date_input("Inicio del contrato")
    fecha_fin_contrato = st.date_input("Fin del contrato")
    tipo_tarifa = st.selectbox("Tipo de tarifa", ["ISS", "SOAT", "CUPS", "Otro"])
    techo_mensual = st.number_input("Techo mensual", min_value=0.0)
    condiciones = st.text_area("Condiciones especiales")
    aseg_opciones = aseguradoras[['id', 'nombre']].drop_duplicates()
    aseg_nombre_map = {row['nombre']: row['id'] for _, row in aseg_opciones.iterrows()}
    nombre_aseg = st.selectbox("Aseguradora", list(aseg_nombre_map.keys()))
    guardar_contrato = st.form_submit_button("Guardar contrato")
    if guardar_contrato:
        aseg_id = aseg_nombre_map[nombre_aseg]
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO contratos (nombre, fecha_inicio, fecha_fin, tipo_tarifa, techo_mensual, condiciones, aseguradora_id)
                VALUES (:nombre, :inicio, :fin, :tipo, :techo, :condiciones, :aseg_id)
            """), {
                "nombre": nombre_contrato,
                "inicio": fecha_inicio_contrato.strftime("%Y-%m-%d"),
                "fin": fecha_fin_contrato.strftime("%Y-%m-%d"),
                "tipo": tipo_tarifa,
                "techo": techo_mensual,
                "condiciones": condiciones,
                "aseg_id": aseg_id
            })
        st.success("✅ Contrato registrado exitosamente.")
        st.experimental_rerun()

# --- Formulario de ingreso de procesos y subprocesos ---
st.subheader("🔧 Crear nuevo proceso / subproceso")
with st.form("form_proceso_sub"):
    nuevo_proceso = st.text_input("Nombre del proceso")
    nuevo_subproceso = st.text_input("Nombre del subproceso")
    guardar_proceso = st.form_submit_button("Guardar proceso y subproceso")
    if guardar_proceso:
        with engine.begin() as conn:
            result = conn.execute(text("INSERT INTO procesos (nombre) VALUES (:nombre)"), {"nombre": nuevo_proceso})
            proceso_id = result.lastrowid
            conn.execute(text("INSERT INTO subprocesos (nombre, proceso_id) VALUES (:nombre, :proc_id)"), {
                "nombre": nuevo_subproceso,
                "proc_id": proceso_id
            })
        st.success("✅ Proceso y subproceso creados.")
        st.experimental_rerun()

# --- Generación y protección de tareas_estado ---
if not tareas.empty:
    tareas_estado = tareas.groupby(['proyecto_id', 'estado']).size().unstack(fill_value=0).reset_index()
    tareas_estado = tareas_estado.merge(proyectos[['id', 'nombre']], left_on='proyecto_id', right_on='id')
    for col in ['Pendiente', 'En curso', 'Finalizada']:
        if col not in tareas_estado.columns:
            tareas_estado[col] = 0
    tareas_estado['total'] = tareas_estado[['Pendiente', 'En curso', 'Finalizada']].sum(axis=1, skipna=True)
    tareas_estado['avance'] = (tareas_estado['Finalizada'] / tareas_estado['total'] * 100).round(1)
else:
    tareas_estado = pd.DataFrame(columns=['proyecto_id', 'Pendiente', 'En curso', 'Finalizada', 'nombre', 'total', 'avance'])

# --- Visualización editable de registros ---
st.subheader("🗂️ Registros actuales")

st.markdown("### Contratos")
st.dataframe(contratos.drop(columns=["id"]).merge(aseguradoras[["id", "nombre"]], left_on="aseguradora_id", right_on="id", suffixes=("", "_aseg"))
            .drop(columns=["id_aseg", "aseguradora_id"]).rename(columns={"nombre_aseg": "Aseguradora"}))

st.markdown("### Procesos")
st.dataframe(procesos.drop(columns=["id"]))

st.markdown("### Subprocesos")
st.dataframe(subprocesos.merge(procesos, left_on="proceso_id", right_on="id", suffixes=("", "_proc"))
            .drop(columns=["id_proc", "proceso_id"]).rename(columns={"nombre_proc": "Proceso"}))

# --- Filtros para informes ---
st.subheader("📌 Filtros de avance de tareas")
col1, col2 = st.columns(2)
with col1:
    filtro_fecha_inicio = st.date_input("Desde", value=pd.to_datetime("2024-01-01"))
with col2:
    filtro_fecha_fin = st.date_input("Hasta", value=pd.to_datetime("today"))

filtro_responsable = st.selectbox("Filtrar por responsable", opciones_responsables := ['Todos'] + sorted(tareas['responsable'].dropna().unique().tolist()) if not tareas.empty else ['Todos'])

filtro_data = tareas.copy()
filtro_data['fecha_inicio'] = pd.to_datetime(filtro_data['fecha_inicio'], errors='coerce')
filtro_data = filtro_data[(filtro_data['fecha_inicio'] >= pd.to_datetime(filtro_fecha_inicio)) &
                           (filtro_data['fecha_inicio'] <= pd.to_datetime(filtro_fecha_fin))]
if filtro_responsable != 'Todos':
    filtro_data = filtro_data[filtro_data['responsable'] == filtro_responsable]

filtro_estado = filtro_data.groupby(['estado']).size().reset_index(name='conteo')
st.markdown("### 🔍 Resumen filtrado")
st.dataframe(filtro_estado)

# --- Visualización gráfica interactiva ---
import plotly.express as px

if not filtro_data.empty:
    st.subheader("📈 Gráfico de avance por responsable")
    avance_responsable = filtro_data.groupby(['responsable', 'estado']).size().reset_index(name='tareas')
    fig = px.bar(avance_responsable, x='responsable', y='tareas', color='estado', title='Estado de tareas por responsable')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗓️ Diagrama de Gantt por proyecto")
    filtro_data['fecha_fin'] = pd.to_datetime(filtro_data['fecha_fin'], errors='coerce')
    filtro_data['descripcion'] = filtro_data['descripcion'].fillna('')
    fig_gantt = px.timeline(
        filtro_data,
        x_start='fecha_inicio',
        x_end='fecha_fin',
        y='descripcion',
        color='estado',
        title='Tareas programadas',
        hover_data=['responsable']
    )
    fig_gantt.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_gantt, use_container_width=True)

# --- Panel de gestión y exportación ---
st.subheader("📊 Exportar avance de tareas")
if not tareas_estado.empty:
    st.download_button("📥 Descargar avance en Excel", data=tareas_estado.to_csv(index=False).encode('utf-8'), file_name="avance_tareas.csv", mime="text/csv")

st.subheader("🛠️ Panel de administración de tareas")
if not tareas.empty:
    tarea_a_eliminar = st.selectbox("Selecciona una tarea para eliminar", tareas["descripcion"] + " (ID: " + tareas["id"].astype(str) + ")")
    if st.button("❌ Eliminar tarea"):
        id_tarea = int(tarea_a_eliminar.split("ID: ")[-1][:-1])
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM tareas WHERE id = :id"), {"id": id_tarea})
        st.success("Tarea eliminada correctamente")
        st.experimental_rerun()
else:
    st.info("No hay tareas disponibles para gestionar.")
