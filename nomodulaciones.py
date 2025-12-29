import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analizador Avanzado 3.30.8", layout="wide")

st.title("📂 Reporte Específico: Hoja 3.30.8")

uploaded_file = st.file_uploader("Sube el archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        hoja_objetivo = "3.30.8"

        if hoja_objetivo in excel_file.sheet_names:
            # 1. Cargar la hoja
            df = pd.read_excel(uploaded_file, sheet_name=hoja_objetivo)

            # --- PROCESAMIENTO DE DATOS ---
            
            # Convertir columna 'Entrega' a fecha (manejando errores)
            df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
            # Eliminar filas donde la fecha no sea válida para el filtro
            df = df.dropna(subset=['Entrega'])

            # --- FILTROS EN BARRA LATERAL ---
            st.sidebar.header("Filtros")
            
            # Filtro de Fechas
            min_date = df['Entrega'].min().date()
            max_date = df['Entrega'].max().date()
            
            fecha_rango = st.sidebar.date_input(
                "Selecciona el rango de Entrega",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            # --- APLICAR FILTROS ---
            
            # Aplicar filtro de fecha (si se seleccionó un rango completo)
            if isinstance(fecha_rango, tuple) and len(fecha_rango) == 2:
                mask_fecha = (df['Entrega'].dt.date >= fecha_rango[0]) & (df['Entrega'].dt.date <= fecha_rango[1])
                df_filtrado = df.loc[mask_fecha]
            else:
                df_filtrado = df.copy()

            # Aplicar filtro DPS == 88
            # (Convertimos a numérico por si acaso viene como texto)
            df_filtrado = df_filtrado[pd.to_numeric(df_filtrado['DPS'], errors='coerce') == 88]

            # --- CÁLCULOS Y VISUALIZACIÓN ---
            
            # Contar valores únicos de CONCATENADO
            conteo_unico = df_filtrado['CONCATENADO'].nunique()

            # Métricas principales
            col1, col2 = st.columns(2)
            col1.metric("Total Filas (DPS 88)", len(df_filtrado))
            col2.metric("Valores Únicos 'CONCATENADO'", conteo_unico)

            st.markdown("---")
            st.subheader(f"Datos filtrados (DPS: 88 | Rango: {fecha_rango})")
            
            if df_filtrado.empty:
                st.warning("No hay datos que coincidan con los filtros seleccionados.")
            else:
                st.dataframe(df_filtrado)

        else:
            st.error(f"No se encontró la hoja '{hoja_objetivo}'")

    except Exception as e:
        st.error(f"Error al procesar: {e}")
