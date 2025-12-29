import streamlit as st
import pandas as pd

st.set_page_config(page_title="Resumen General 3.30.8", layout="centered")

st.title("📊 Resumen General por Fechas")
st.write("Análisis de Modulación (DPS 88) de la hoja 3.30.8")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha'] = df['Entrega'].dt.date
        
        # Filtro base permanente: Solo DPS 88
        df_base = df[df['DPS'].astype(str).str.contains('88')].copy()

        # Función para identificar si el valor en BUSCA es un número válido (no error)
        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "error" in str(valor).lower() or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        # Identificar filas moduladas
        df_base['es_modulado'] = df_base['BUSCA'].apply(es_valido)

        # --- GENERACIÓN DE LA TABLA RESUMEN ---
        resumen = df_base.groupby('Fecha').apply(
            lambda x: pd.Series({
                'Total Concatenados': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        # --- NUEVA COLUMNA: % DE MODULACIÓN ---
        # Evitamos división por cero con .where o simplemente asegurando que haya datos
        resumen['% Modulación'] = (resumen['Modulados'] / resumen['Total Concatenados']) * 100

        # Ordenar por fecha más reciente
        resumen = resumen.sort_values(by='Fecha', ascending=False)

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        
        st.subheader("Tabla Comparativa con Porcentajes")
        
        # Formateo visual de la tabla
        st.dataframe(
            resumen.style.format({
                'Fecha': lambda x: x.strftime('%d/%m/%Y'),
                'Total Concatenados': '{:,.0f}',
                'Modulados': '{:,.0f}',
                '% Modulación': '{:.2f}%'
            }), 
            use_container_width=True,
            hide_index=True
        )

        # Botón para descargar el resumen completo
        csv = resumen.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar esta tabla (CSV)",
            data=csv,
            file_name="resumen_modulacion_3308.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error: Asegúrate de que el archivo tenga las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA'.")
