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

        # --- PROCESAMIENTO ---
        # Convertir 'Entrega' a fecha y quitar filas inválidas
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

        # --- LÓGICA DE FILTRADO BASE (Fecha y DPS 88) ---
        df_base = df[
            (df['Fecha_Corta'] == fecha_elegida) & 
            (df['DPS'].astype(str).str.contains('88'))
        ]

        # 1. Conteo Concatenados (Total del filtro base)
        conteo_total_concatenado = df_base['CONCATENADO'].nunique()

        # 2. Conteo Modulados (BUSCA con número válido y no error)
        # Filtramos valores no numéricos, nulos o errores comunes de Excel
        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "error" in str(valor).lower() or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        # Aplicamos la máscara de validez sobre el filtro base
        mask_busca_valido = df_base['BUSCA'].apply(es_valido)
        df_modulados = df_base[mask_busca_valido]
        
        conteo_modulados = df_modulados['CONCATENADO'].nunique()

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Total Concatenados", value=conteo_total_concatenado)
            
        with col2:
            st.metric(label="Modulados", value=conteo_modulados)
            
        st.caption(f"Filtros aplicados: Hoja 3.30.8 | Fecha: {fecha_elegida.strftime('%d/%m/%Y')} | DPS: 88")

    except Exception as e:
        st.error(f"Error: Revisa que el archivo tenga las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA'.")
