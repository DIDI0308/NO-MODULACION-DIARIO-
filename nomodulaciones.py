import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analizador Avanzado 3.30.8", layout="wide")

st.title("📊 Análisis Específico - Hoja 3.30.8")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Verificar si existe la hoja
        excel_file = pd.ExcelFile(uploaded_file)
        if "3.30.8" in excel_file.sheet_names:
            
            # Leer la hoja específica
            # Nota: Si tus columnas no tienen encabezados, añade header=None
            df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

            # --- PROCESAMIENTO DE DATOS ---
            
            # Convertir columna 'x' a fecha (manejando errores)
            df['x'] = pd.to_datetime(df['x'], errors='coerce')
            
            # --- FILTROS EN BARRA LATERAL ---
            st.sidebar.header("Filtros de Datos")
            
            # Filtro de Fechas (Columna X)
            min_date = df['x'].min().date() if not df['x'].dropna().empty else None
            max_date = df['x'].max().date() if not df['x'].dropna().empty else None
            
            if min_date and max_date:
                fecha_rango = st.sidebar.date_input(
                    "Selecciona rango de fechas (Columna X)",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                st.sidebar.warning("No se detectaron fechas válidas en la columna 'x'")
                fecha_rango = None

            # --- APLICACIÓN DE FILTROS ---
            
            # 1. Filtro de columna 'am' == 88
            df_filtrado = df[df['am'] == 88]
            
            # 2. Filtro de rango de fechas
            if fecha_rango and len(fecha_rango) == 2:
                start_date, end_date = fecha_rango
                df_filtrado = df_filtrado[
                    (df_filtrado['x'].dt.date >= start_date) & 
                    (df_filtrado['x'].dt.date <= end_date)
                ]

            # --- VISUALIZACIÓN Y MÉTRICAS ---
            
            col1, col2 = st.columns(2)
            
            # Conteo de valores únicos en columna 'a'
            valores_unicos_a = df_filtrado['a'].nunique()
            
            with col1:
                st.metric("Valores únicos en 'a'", valores_unicos_a)
            with col2:
                st.metric("Registros encontrados", len(df_filtrado))

            st.markdown("---")
            st.subheader("Datos Filtrados")
            st.write(f"Mostrando registros donde **am = 88** y fecha está en el rango seleccionado.")
            st.dataframe(df_filtrado)

        else:
            st.error("No se encontró la hoja '3.30.8' en el archivo.")
            
    except Exception as e:
        st.error(f"Error al procesar: {e}")
        st.info("Asegúrate de que las columnas 'x', 'am' y 'a' existan en la hoja.")
