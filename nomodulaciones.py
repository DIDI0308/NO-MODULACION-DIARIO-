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

        # --- FILTRADO BASE (Fecha y DPS 88) ---
        df_base = df[
            (df['Fecha_Corta'] == fecha_elegida) & 
            (df['DPS'].astype(str).str.contains('88'))
        ].copy()

        # --- CÁLCULO 1: TOTAL CONCATENADOS ---
        conteo_total_unico = df_base['CONCATENADO'].nunique()

        # --- CÁLCULO 2: MODULADOS (Filtro columna BUSCA) ---
        # Convertimos a numérico, lo que no sea número se vuelve NaN
        df_base['BUSCA_LIMPIA'] = pd.to_numeric(df_base['BUSCA'], errors='coerce')
        
        # Filtramos solo donde BUSCA es un número válido y no es nulo/error
        df_modulados = df_base[df_base['BUSCA_LIMPIA'].notnull()]
        
        # Contamos únicos de CONCATENADO para estos modulados
        conteo_modulados = df_modulados['CONCATENADO'].nunique()

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="Total Concatenados (DPS 88)", 
                value=conteo_total_unico
            )
            
        with col2:
            st.metric(
                label="Modulados", 
                value=conteo_modulados,
                help="Conteo de Concatenados donde 'BUSCA' es un número válido"
            )

        st.caption(f"Fecha consultada: {fecha_elegida.strftime('%d/%m/%Y')}")

    except Exception as e:
        st.error(f"Error: Asegúrate de que las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA' existan.")
