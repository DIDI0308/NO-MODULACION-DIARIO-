import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analizador Avanzado", layout="wide")

st.title("📂 Procesador de Hoja 3.30.8")

uploaded_file = st.file_uploader("Elige un archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        hoja_objetivo = "3.30.8"

        if hoja_objetivo in excel_file.sheet_names:
            # 1. Leer la hoja
            df = pd.read_excel(uploaded_file, sheet_name=hoja_objetivo)

            # Asegurar que la columna X sea de tipo fecha (ajustar nombre si tiene espacios)
            if 'X' in df.columns:
                df['X'] = pd.to_datetime(df['X'], errors='coerce')
                
                # --- SECCIÓN DE FILTROS EN EL LATERAL (SIDEBAR) ---
                st.sidebar.header("Filtros")
                
                # Filtro por fechas (Columna X)
                min_date = df['X'].min().date()
                max_date = df['X'].max().date()
                
                fecha_rango = st.sidebar.date_input(
                    "Selecciona rango de fechas (Columna X)",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )

                # --- APLICAR FILTROS ---
                # Aplicar filtro de fecha
                if len(fecha_rango) == 2:
                    start_date, end_date = fecha_rango
                    mask = (df['X'].dt.date >= start_date) & (df['X'].dt.date <= end_date)
                    df_filtrado = df.loc[mask]
                else:
                    df_filtrado = df.copy()

                # Filtro Columna AM == 88
                if 'AM' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['AM'] == 88]
                else:
                    st.error("No se encontró la columna 'AM'")

                # --- RESULTADOS ---
                st.subheader(f"📊 Resultados para hoja {hoja_objetivo}")
                
                # Contar valores únicos de la Columna A
                if 'A' in df_filtrado.columns:
                    conteo_unicos = df_filtrado['A'].nunique()
                    
                    # Mostrar métrica destacada
                    col1, col2 = st.columns(2)
                    col1.metric("Valores únicos en Columna A", conteo_unicos)
                    col2.metric("Total filas filtradas", len(df_filtrado))
                    
                    st.markdown("---")
                    st.write("Vista previa de los datos filtrados:")
                    st.dataframe(df_filtrado)
                else:
                    st.error("No se encontró la columna 'A'")
            
            else:
                st.error("La columna 'X' no existe en esta hoja.")
        else:
            st.error(f"La hoja '{hoja_objetivo}' no existe.")

    except Exception as e:
        st.error(f"Error: {e}")
