
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
