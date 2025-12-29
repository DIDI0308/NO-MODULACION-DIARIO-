import streamlit as st
import pandas as pd

st.set_page_config(page_title="Resumen por Fechas 3.30.8", layout="centered")

st.title("📊 Resumen General por Fechas")
st.write("Conteo de Concatenados y Modulados (DPS 88) de la hoja 3.30.8")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO ---
        # Convertir 'Entrega' a fecha y quitar filas inválidas
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
        # Agrupamos por fecha y calculamos los unicos de CONCATENADO para cada caso
        resumen = df_base.groupby('Fecha').apply(
            lambda x: pd.Series({
                'Total Concatenados': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        # Ordenar por fecha más reciente
        resumen = resumen.sort_values(by='Fecha', ascending=False)

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        
        # Mostrar la tabla formateada
        st.subheader("Tabla Comparativa")
        st.dataframe(
            resumen.style.format({
                'Fecha': lambda x: x.strftime('%d/%m/%Y'),
                'Total Concatenados': '{:,}',
                'Modulados': '{:,}'
            }), 
            use_container_width=True,
            hide_index=True
        )

        # Botón para descargar el resumen completo
        csv = resumen.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar esta tabla (CSV)",
            data=csv,
            file_name="resumen_fechas_3308.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error: Asegúrate de que el archivo tenga las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA'.")
