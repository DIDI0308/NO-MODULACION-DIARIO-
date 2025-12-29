import streamlit as st
import pandas as pd

st.set_page_config(page_title="Contador 3.30.8", layout="centered")

st.title("📂 Contador de Concatenados")

uploaded_file = st.file_uploader("Sube el archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Leer la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PREPARACIÓN RÁPIDA ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha_Corta'] = df['Entrega'].dt.date

        # --- FILTRO DEBAJO DEL TITULO ---
        lista_fechas = sorted(df['Fecha_Corta'].unique(), reverse=True)
        
        fecha_elegida = st.selectbox(
            "Selecciona la fecha de Entrega:",
            options=lista_fechas,
            format_func=lambda x: x.strftime('%d / %m / %Y')
        )

        # --- LÓGICA DE FILTRADO Y CONTEO ---
        # Filtro por fecha y DPS 88
        mask = (df['Fecha_Corta'] == fecha_elegida) & (df['DPS'].astype(str) == '88')
        df_filtrado = df.loc[mask]
        
        # Conteo de valores únicos
        conteo_unico = df_filtrado['CONCATENADO'].nunique()

        # --- MOSTRAR SOLO EL RESULTADO ---
        st.markdown("---")
        st.metric(label=f"Valores únicos de CONCATENADO (DPS 88)", value=conteo_unico)
        st.markdown("---")

    except Exception as e:
        st.error(f"Error: Asegúrate de que la hoja se llame '3.30.8' y contenga las columnas 'Entrega', 'DPS' y 'CONCATENADO'.")
