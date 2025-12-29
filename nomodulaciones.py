import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Contador 3.30.8", layout="centered")

st.title("📂 Cargador de Base de Datos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO INICIAL ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha_Corta'] = df['Entrega'].dt.date
        
        # --- FILTRO DE FECHA (Debajo del título) ---
        lista_fechas = sorted(df['Fecha_Corta'].unique(), reverse=True)
        
        fecha_elegida = st.selectbox(
            "Selecciona la fecha de Entrega:",
            options=lista_fechas,
            format_func=lambda x: x.strftime('%d/%m/%Y')
        )

        # --- LÓGICA DE FILTRADO ---
        # 1. Filtrar por fecha elegida Y por DPS igual a 88
        df_base = df[
            (df['Fecha_Corta'] == fecha_elegida) & 
            (df['DPS'].astype(str).str.contains('88'))
        ]

        # 2. Conteo de CONCATENADO (Valores únicos)
        conteo_unico = df_base['CONCATENADO'].nunique()

        # 3. Conteo de MODULADOS (Columna BUSCA con número válido)
        # Convertimos a numérico, los errores se vuelven NaN y luego los eliminamos para contar
        modulados_df = df_base.copy()
        modulados_df['BUSCA_NUM'] = pd.to_numeric(modulados_df['BUSCA'], errors='coerce')
        conteo_modulados = modulados_df['BUSCA_NUM'].dropna().count()

        # --- VISUALIZACIÓN DE DATOS ---
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Concatenados Únicos", value=conteo_unico)
            st.caption("Filtro: Fecha y DPS 88")

        with col2:
            st.metric(label="Modulados", value=int(conteo_modulados))
            st.caption("Filtro: BUSCA (Números válidos)")

    except Exception as e:
        st.error(f"Error: Revisa que existan las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA'.")
