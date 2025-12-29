import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analizador 3.30.8", layout="wide")

st.title("📂 Reporte por Fecha Específica - Hoja 3.30.8")

uploaded_file = st.file_uploader("Sube el archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- LIMPIEZA Y CONVERSIÓN ---
        # Convertir columna 'Entrega' a formato fecha
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        # Eliminar filas con fechas inválidas o nulas
        df = df.dropna(subset=['Entrega'])

        # --- FILTROS EN LA BARRA LATERAL ---
        st.sidebar.header("Configuración de Filtros")
        
        # Obtener las fechas disponibles para ayudar al usuario
        fechas_disponibles = sorted(df['Entrega'].dt.date.unique())
        
        # Widget para seleccionar UNA fecha específica
        fecha_seleccionada = st.sidebar.date_input(
            "Selecciona el día de Entrega",
            value=fechas_disponibles[-1] if fechas_disponibles else None, # Por defecto la última fecha
            min_value=min(fechas_disponibles) if fechas_disponibles else None,
            max_value=max(fechas_disponibles) if fechas_disponibles else None
        )

        # --- APLICACIÓN DE FILTROS ---
        
        # Filtro 1: Fecha específica
        df_filtrado = df[df['Entrega'].dt.date == fecha_seleccionada]
        
        # Filtro 2: DPS solo sea 88
        df_filtrado = df_filtrado[pd.to_numeric(df_filtrado['DPS'], errors='coerce') == 88]

        # --- CÁLCULOS ---
        
        # Contar valores únicos de la columna CONCATENADO
        conteo_unico = df_filtrado['CONCATENADO'].nunique()
        total_registros = len(df_filtrado)

        # --- VISUALIZACIÓN DE RESULTADOS ---
        
        st.info(f"📅 Resultados para el día: **{fecha_seleccionada}**")
        
        # Mostrar métricas destacadas
        m1, m2 = st.columns(2)
        m1.metric("Valores Únicos (CONCATENADO)", conteo_unico)
        m2.metric("Total Filas (DPS 88)", total_registros)

        st.markdown("---")
        
        if not df_filtrado.empty:
            st.subheader("Vista previa de los datos filtrados")
            st.dataframe(df_filtrado)
        else:
            st.warning(f"No hay datos con DPS 88 para la fecha {fecha_seleccionada}.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
