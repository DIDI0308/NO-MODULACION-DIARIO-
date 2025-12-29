import streamlit as st
import pandas as pd

st.set_page_config(page_title="Contador Modulados 3.30.8", layout="centered")

st.title("📂 Cargador de Base de Datos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PRE-PROCESAMIENTO ---
        # Convertir 'Entrega' a fecha
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha_Corta'] = df['Entrega'].dt.date
        
        # --- FILTRO DE FECHA (Interfaz principal) ---
        lista_fechas = sorted(df['Fecha_Corta'].unique(), reverse=True)
        fecha_elegida = st.selectbox(
            "Selecciona la fecha de Entrega:",
            options=lista_fechas,
            format_func=lambda x: x.strftime('%d/%m/%Y')
        )

        # --- LÓGICA DE FILTRADO ---
        
        # 1. Filtro por Fecha y DPS 88
        mask_base = (df['Fecha_Corta'] == fecha_elegida) & (df['DPS'].astype(str).str.contains('88'))
        df_base = df[mask_base]

        # 2. Filtro columna BUSCA (Solo números válidos, no errores)
        # pd.to_numeric con errors='coerce' convierte errores/texto en NaN, luego dropna los elimina
        df_modulados = df_base.copy()
        df_modulados['BUSCA_NUM'] = pd.to_numeric(df_modulados['BUSCA'], errors='coerce')
        df_modulados = df_modulados.dropna(subset=['BUSCA_NUM'])

        # --- CÁLCULOS ---
        # Conteo de valores únicos de la columna CONCATENADO para los "Modulados"
        conteo_modulados = df_modulados['CONCATENADO'].nunique()

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        
        # Mostramos el dato solicitado
        st.metric(label="Modulados", value=conteo_modulados)
        
        st.caption(f"Filtros aplicados: Hoja 3.30.8 | Fecha: {fecha_elegida.strftime('%d/%m/%Y')} | DPS: 88 | BUSCA: Numérico válido")

    except Exception as e:
        st.error(f"Error: Revisa que el archivo tenga las columnas 'Entrega', 'DPS', 'BUSCA' y 'CONCATENADO'.")
