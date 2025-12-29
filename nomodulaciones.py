import streamlit as st
import pandas as pd

st.set_page_config(page_title="Resumen por Fecha 3.30.8", layout="centered")

st.title("📂 Resumen de Datos por Fecha")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO INICIAL ---
        # Limpieza de fechas
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha'] = df['Entrega'].dt.date

        # Filtro base: Solo DPS 88
        df_base = df[df['DPS'].astype(str).str.contains('88')].copy()

        # Función para validar si la columna BUSCA tiene un número válido
        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        # Identificar filas moduladas (BUSCA válido)
        df_base['Es_Modulado'] = df_base['BUSCA'].apply(es_valido)

        # --- CREACIÓN DE LA TABLA RESUMEN ---
        # Agrupamos por fecha y calculamos los dos datos solicitados
        resumen = df_base.groupby('Fecha').apply(lambda x: pd.Series({
            'Total Concatenados': x['CONCATENADO'].nunique(),
            'Modulados': x[x['Es_Modulado'] == True]['CONCATENADO'].nunique()
        })).reset_index()

        # Ordenar por fecha más reciente
        resumen = resumen.sort_values(by='Fecha', ascending=False)

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        st.subheader("📊 Tabla Comparativa por Fecha (DPS 88)")
        
        # Mostramos la tabla formateada
        st.dataframe(
            resumen, 
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha de Entrega", format="DD/MM/YYYY"),
                "Total Concatenados": st.column_config.NumberColumn("Total Concatenados"),
                "Modulados": st.column_config.NumberColumn("Modulados")
            },
            hide_index=True,
            use_container_width=True
        )

        # Totales generales de la tabla
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("Total General Concatenados", int(resumen['Total Concatenados'].sum()))
        c2.metric("Total General Modulados", int(resumen['Modulados'].sum()))

    except Exception as e:
        st.error(f"Error: Asegúrate de que la hoja 3.30.8 tenga las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA'.")
