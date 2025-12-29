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

        # --- APLICACIÓN DE FILTROS BASE (Fecha y DPS 88) ---
        df_base = df[
            (df['Fecha_Corta'] == fecha_elegida) & 
            (df['DPS'].astype(str).str.contains('88'))
        ]

        # --- CÁLCULOS ---
        
        # 1. Conteo de Concatenados Únicos
        conteo_unico = df_base['CONCATENADO'].nunique()

        # 2. Conteo de "Modulados" (Columna BUSCA con número válido)
        # Convertimos a numérico: lo que no es número se vuelve NaN
        busqueda_numerica = pd.to_numeric(df_base['BUSCA'], errors='coerce')
        # Contamos solo los que no son nulos (números válidos)
        conteo_modulados = busqueda_numerica.notnull().sum()

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Únicos CONCATENADO", value=conteo_unico)
            
        with col2:
            st.metric(label="Modulados", value=int(conteo_modulados))

        st.caption(f"Filtros aplicados: Fecha {fecha_elegida.strftime('%d/%m/%Y')} y DPS 88")

    except Exception as e:
        st.error(f"Error: Revisa que las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA' existan.")
