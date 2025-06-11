import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Configuración
st.set_page_config(page_title="CRM Clínica de Ortopedia", layout="wide")
st.title("📋 CRM Clínica de Ortopedia")

# Conexión a base de datos SQLite (local)
engine = create_engine("sqlite:///crm_clinica.db")

# --- Cargar datos ---
@st.cache_data
def cargar_datos():
    aseguradoras = pd.read_sql("SELECT * FROM aseguradoras", engine)
    contratos = pd.read_sql("SELECT * FROM contratos", engine)
    return aseguradoras, contratos

aseguradoras, contratos = cargar_datos()

# --- Pestañas ---
tab1, tab2, tab3 = st.tabs(["🔍 Contratos", "📈 Informes", "➕ Nueva aseguradora"])

with tab1:
    st.subheader("Contratos registrados")
    contratos = contratos.merge(aseguradoras[["id", "nombre"]], left_on="aseguradora_id", right_on="id", suffixes=("", "_aseg"))
    contratos.drop(columns=["id_aseg"], inplace=True)
    st.dataframe(contratos)

with tab2:
    st.subheader("📊 Informes estratégicos")
    resumen = contratos.groupby("nombre").agg(
        total_contratos=('id', 'count'),
        total_techo=('techo_mensual', 'sum')
    ).reset_index()
    st.metric("Total aseguradoras", len(resumen))
    st.dataframe(resumen)

    # Vencimientos próximos
    from datetime import datetime, timedelta
    contratos["fecha_fin"] = pd.to_datetime(contratos["fecha_fin"])
    proximos = contratos[contratos["fecha_fin"] <= datetime.today() + timedelta(days=30)]
    st.warning("Contratos con vencimiento en los próximos 30 días")
    st.dataframe(proximos)

with tab3:
    st.subheader("Registrar nueva aseguradora")
    with st.form("form_aseg"):
        nombre = st.text_input("Nombre")
        nit = st.text_input("NIT")
        contacto = st.text_input("Contacto")
        submitted = st.form_submit_button("Guardar")
        if submitted:
            with engine.begin() as conn:
                conn.execute(f"""
                    INSERT INTO aseguradoras (nombre, nit, contacto)
                    VALUES ('{nombre}', '{nit}', '{contacto}')
                """)
            st.success("Aseguradora registrada correctamente")
            st.experimental_rerun()
