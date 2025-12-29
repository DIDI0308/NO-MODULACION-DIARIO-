import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analizador 3.30.8", layout="wide")

st.title("📂 Reporte Selectivo - Hoja 3.30.8")
st.write("Filtro por fecha específica, DPS 88 y conteo de Concatenados.")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Leer la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PREPARACIÓN DE DATOS ---
        # Asegurar que 'Entrega' sea fecha
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        # Quitar filas sin fecha
        df = df.dropna(subset=['Entrega'])
        
        # Crear una columna solo con la fecha (sin hora) para el filtro
        df['Fecha_Corta'] = df['Entrega'].dt.date

        # --- PANEL LATERAL DE FILTROS ---
        st.sidebar.header("Opciones de Filtrado")
        
        # Obtener lista de fechas únicas y ordenarlas
        lista_fechas = sorted(df['Fecha_Corta'].unique(), reverse=True)
        
        # Selector de fecha (Menú desplegable)
        fecha_elegida = st.sidebar.selectbox(
            "Selecciona una fecha disponible:",
            options=lista_fechas,
            format_func=lambda x: x.strftime('%d / %m / %Y') # Formato visual más limpio
        )

        # --- LÓGICA DE FILTRADO ---
        
        # Filtrar por la fecha elegida
        df_filtrado = df[df['Fecha_Corta'] == fecha_elegida]
        
        # Filtrar permanentemente por DPS 88
        # Usamos string por si el Excel lo trata como texto o número
        df_filtrado = df_filtrado[df_filtrado['DPS'].astype(str) == '88']

        # --- RESULTADOS Y MÉTRICAS ---
        
        st.subheader(f"📅 Reporte del día: {fecha_elegida.strftime('%d de %B, %Y')}")
        
        # Cálculo de valores únicos
        conteo_unico = df_filtrado['CONCATENADO'].nunique()
        total_filas = len(df_filtrado)

        # Mostrar en tarjetas visuales
        col1, col2, col3 = st.columns(3)
        col1.metric("Únicos (CONCATENADO)", conteo_unico)
        col2.metric("Total Filas (DPS 88)", total_filas)
        col3.metric("Fecha", fecha_elegida.strftime('%d/%m/%Y'))

        st.markdown("---")

        if not df_filtrado.empty:
            st.write("### Detalle de los datos")
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Botón para descargar solo este reporte
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar este reporte (CSV)",
                data=csv,
                file_name=f"reporte_{fecha_elegida}.csv",
                mime="text/csv",
            )
        else:
            st.warning(f"No se encontraron registros con DPS 88 para el día {fecha_elegida}")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        st.info("Asegúrate de que las columnas 'Entrega', 'DPS' y 'CONCATENADO' existan en la hoja 3.30.8")
