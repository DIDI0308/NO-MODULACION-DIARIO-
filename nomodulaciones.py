import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Modulación 3.30.8", layout="wide")

st.title("📊 Análisis de Modulación y Detalle de Errores")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO BASE ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha_Corta'] = df['Entrega'].dt.date
        
        # Filtro permanente: Solo DPS 88
        df_base = df[df['DPS'].astype(str).str.contains('88')].copy()

        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "error" in str(valor).lower() or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        # Identificamos modulados y errores
        df_base['es_modulado'] = df_base['BUSCA'].apply(es_valido)
        # Filtro de registros con ERROR (lo opuesto a válido)
        df_errores = df_base[df_base['es_modulado'] == False].copy()

        # --- SECCIÓN 1: GRÁFICO (Mantiene filtros anteriores) ---
        st.markdown("### 📈 Evolución de Modulación")
        opcion_periodo = st.selectbox(
            "Selecciona el periodo para el gráfico:",
            ["Últimos 7 días", "Mes Actual (Calendario)", "Promedio Mensual (Histórico)"]
        )

        ultima_fecha = df_base['Entrega'].max()
        
        if opcion_periodo == "Últimos 7 días":
            fecha_limite = (ultima_fecha - pd.Timedelta(days=7)).date()
            df_graf = df_base[df_base['Fecha_Corta'] > fecha_limite]
            agrupar_por = 'Fecha_Corta'
        elif opcion_periodo == "Mes Actual (Calendario)":
            df_graf = df_base[(df_base['Entrega'].dt.month == ultima_fecha.month) & (df_base['Entrega'].dt.year == ultima_fecha.year)]
            agrupar_por = 'Fecha_Corta'
        else:
            df_graf = df_base.copy()
            df_graf['Periodo'] = df_base['Entrega'].dt.to_period('M').astype(str)
            agrupar_por = 'Periodo'

        resumen_graf = df_graf.groupby(agrupar_por).apply(
            lambda x: pd.Series({'% Modulación': (x[x['es_modulado']]['CONCATENADO'].nunique() / x['CONCATENADO'].nunique()) * 100})
        ).reset_index()

        fig = px.bar(resumen_graf, x=agrupar_por, y='% Modulación', text='% Modulación', 
                     color_discrete_sequence=['#FFD700'], height=400)
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(yaxis=dict(range=[0, 115]), xaxis={'type': 'category'})
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 2: DETALLE DE ERRORES POR FECHA ---
        st.markdown("---")
        st.subheader("🔍 Detalle de Registros con Error en BUSCA")
        
        # Filtro visual de fecha única
        fechas_disponibles = sorted(df_base['Fecha_Corta'].unique(), reverse=True)
        fecha_seleccionada = st.selectbox("Elige una fecha para ver los errores:", fechas_disponibles)

        # Filtrar tabla por fecha y por los que TIENEN ERROR
        tabla_detalle = df_errores[df_errores['Fecha_Corta'] == fecha_seleccionada]
        
        # Seleccionar solo las columnas pedidas
        columnas_visibles = ['Client', 'F.Pedido', 'Motivo']
        
        # Verificar que las columnas existan antes de mostrar
        cols_existentes = [c for c in columnas_visibles if c in tabla_detalle.columns]

        if not tabla_detalle.empty:
            st.warning(f"Se encontraron {len(tabla_detalle)} registros con error para el día {fecha_seleccionada.strftime('%d/%m/%Y')}")
            st.dataframe(tabla_detalle[cols_existentes], use_container_width=True, hide_index=True)
        else:
            st.success(f"No hay errores en la columna BUSCA para la fecha {fecha_seleccionada.strftime('%d/%m/%Y')}")

    except Exception as e:
        st.error(f"Hubo un problema al procesar los datos: {e}")
