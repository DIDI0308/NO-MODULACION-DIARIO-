import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Modulación 3.30.8", layout="wide")

st.title("📊 Control de Modulación y Errores")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO GENERAL ---
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

        # Identificar qué es válido y qué es error
        df_base['es_modulado'] = df_base['BUSCA'].apply(es_valido)

        # ==========================================
        # SECCIÓN 1: GRÁFICO DE PORCENTAJE (OCULTO LA TABLA)
        # ==========================================
        st.header("1. Evolución de Modulación")
        opcion_periodo = st.selectbox(
            "Selecciona el periodo para el gráfico:",
            ["Últimos 7 días", "Mes Actual (Calendario)", "Promedio Mensual (Histórico)"]
        )

        ultima_fecha = df_base['Entrega'].max()
        
        if opcion_periodo == "Últimos 7 días":
            fecha_limite = (ultima_fecha - pd.Timedelta(days=7)).date()
            df_graf = df_base[df_base['Fecha'] > fecha_limite]
            agrupar_por = 'Fecha'
        elif opcion_periodo == "Mes Actual (Calendario)":
            df_graf = df_base[(df_base['Entrega'].dt.month == ultima_fecha.month) & 
                               (df_base['Entrega'].dt.year == ultima_fecha.year)]
            agrupar_por = 'Fecha'
        else:
            df_graf = df_base.copy()
            df_graf['Periodo'] = df_base['Entrega'].dt.to_period('M').astype(str)
            agrupar_por = 'Periodo'

        resumen = df_graf.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Total': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        resumen['Porcentaje'] = (resumen['Modulados'] / resumen['Total']) * 100
        
        fig = px.bar(resumen.sort_values(agrupar_por), x=agrupar_por, y='Porcentaje', 
                     text='Porcentaje', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(yaxis_title="% Modulación", yaxis=dict(range=[0, 115]), xaxis={'type': 'category'})
        st.plotly_chart(fig, use_container_width=True)


        # ==========================================
        # SECCIÓN 2: TABLA DE ERRORES (DETALLE POR FECHA)
        # ==========================================
        st.markdown("---")
        st.header("2. Detalle de Registros con Error")
        
        # Filtro visual de fecha única para la tabla de errores
        fechas_disponibles = sorted(df_base['Fecha'].unique(), reverse=True)
        fecha_error_sel = st.selectbox("Selecciona fecha para ver Errores:", fechas_disponibles)

        # 1. Filtrar por la fecha seleccionada
        # 2. Filtrar solo los que NO son modulados (errores en BUSCA)
        df_errores = df_base[(df_base['Fecha'] == fecha_error_sel) & (~df_base['es_modulado'])].copy()

        if df_errores.empty:
            st.success(f"No se encontraron errores para la fecha {fecha_error_sel}")
        else:
            # Eliminar duplicados por la columna 'Client', dejando solo el primero
            # Seleccionar solo las columnas solicitadas
            df_errores_final = df_errores.drop_duplicates(subset=['Client'], keep='first')
            
            columnas_finales = ['Client', 'F.Pedido', 'Motivo']
            
            # Verificar que las columnas existan antes de mostrar
            columnas_existentes = [col for col in columnas_finales if col in df_errores_final.columns]
            
            st.write(f"Mostrando motivos de error para {len(df_errores_final)} clientes únicos:")
            st.dataframe(df_errores_final[columnas_existentes], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
