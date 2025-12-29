import streamlit as st
import pandas as pd

st.set_page_config(page_title="Contador 3.30.8", layout="centered")

st.title("📂 Cargador de Base de Datos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO ---
        # Convertir 'Entrega' a fecha y 'DPS' a texto para evitar errores de tipo
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
        # Filtramos por fecha elegida Y por DPS igual a 88
        df_filtrado = df[
            (df['Fecha_Corta'] == fecha_elegida) & 
            (df['DPS'].astype(str).str.contains('88'))
        ]

        # --- RESULTADO ÚNICO ---
        conteo_unico = df_filtrado['CONCATENADO'].nunique()

        st.markdown("---")
        st.metric(label=f"Valores únicos de 'CONCATENADO' (DPS 88)", value=conteo_unico)
        st.caption(f"Fecha consultada: {fecha_elegida.strftime('%d/%m/%Y')}")

    except Exception as e:
        st.error(f"Error: Asegúrate de que la hoja se llame '3.30.8' y contenga las columnas 'Entrega', 'DPS' y 'CONCATENADO'.")
