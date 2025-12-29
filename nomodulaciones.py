import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Modulación 3.30.8", layout="wide")

st.title("📊 Análisis de Modulación por Periodos")

# Recordatorio: El archivo requirements.txt debe tener: pandas, openpyxl, plotly, streamlit
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")
        
        # LIMPIEZA DE ENCABEZADOS (Para encontrar "Motivo    " sí o sí)
        df.columns = df.columns.str.strip()

        # --- PROCESAMIENTO ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha'] = df['Entrega'].dt.date
        
        # Filtro base permanente: Solo DPS 88
        df_base = df[df['DPS'].astype(str).str.contains('88')].copy()

        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "error" in str(valor).lower() or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        df_base['es_modulado'] = df_base['BUSCA'].apply(es_valido)

        # --- SECCIÓN 1: GRÁFICO (TABLA OCULTA) ---
        st.markdown("### 📈 Evolución de Modulación")
        opcion_graf = st.selectbox("Selecciona periodo:", ["Últimos 7 días", "Mes Actual (Calendario)", "Promedio Mensual (Histórico)"])

        ultima_fecha = df_base['Entrega'].max()
        if opcion_graf == "Últimos 7 días":
            df_g = df_base[df_base['Fecha'] > (ultima_fecha - pd.Timedelta(days=7)).date()]
            agrupar = 'Fecha'
        elif opcion_graf == "Mes Actual (Calendario)":
            df_g = df_base[(df_base['Entrega'].dt.month == ultima_fecha.month) & (df_base['Entrega'].dt.year == ultima_fecha.year)]
            agrupar = 'Fecha'
        else:
            df_g = df_base.copy()
            df_g['Periodo'] = df_base['Entrega'].dt.to_period('M').astype(str)
            agrupar = 'Periodo'

        resumen_graf = df_g.groupby(agrupar).apply(lambda x: pd.Series({
            'Total': x['CONCATENADO'].nunique(),
            'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
        })).reset_index()
        resumen_graf['% Modulación'] = (resumen_graf['Modulados'] / resumen_graf['Total']) * 100

        fig = px.bar(resumen_graf.sort_values(agrupar), x=agrupar, y='% Modulación', text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(yaxis=dict(range=[0, 115]), xaxis={'type': 'category'})
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 2: CLIENTES (TÍTULOS SOLICITADOS) ---
        st.markdown("---")
        st.header("Clientes")
        st.subheader("Clientes No Modulados")
        
        # Filtramos los que NO son modulados
        df_no_modulados = df_base[df_base['es_modulado'] == False].copy()

        if not df_no_modulados.empty:
            fechas_disponibles = sorted(df_no_modulados['Fecha'].unique(), reverse=True)
            fecha_filtro = st.selectbox("Selecciona una fecha para ver el detalle:", fechas_disponibles)

            # Filtrar por fecha
            df_detalle = df_no_modulados[df_no_modulados['Fecha'] == fecha_filtro].copy()

            # Asegurar visualización de la columna Motivo (convertir a texto para que aparezca sí o sí)
            if 'Motivo' in df_detalle.columns:
                df_detalle['Motivo'] = df_detalle['Motivo'].astype(str).replace(['nan', 'None', ''], 'Sin información')
            else:
                # En caso de que el strip() falle por caracteres extraños, buscamos por posición
                df_detalle['Motivo'] = "Columna no encontrada"

            # REGLA: Sin repetidos por 'Client', manteniendo solo el primero
            resultado_final = df_detalle.drop_duplicates(subset=['Client'], keep='first')

            # Definición de columnas a mostrar
            cols_a_mostrar = ['Client', 'F.Pedido', 'Motivo']
            
            # Verificación de existencia de columnas para evitar errores de ejecución
            cols_existentes = [c for c in cols_a_mostrar if c in resultado_final.columns]

            st.write(f"Resultados para el día {fecha_filtro}:")
            st.dataframe(resultado_final[cols_existentes], use_container_width=True, hide_index=True)
            
        else:
            st.success("No hay datos de clientes no modulados para mostrar.")

    except Exception as e:
        st.error(f"Error: {e}")
