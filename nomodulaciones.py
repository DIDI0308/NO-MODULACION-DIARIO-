import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Modulación 3.30.8", layout="wide")

# RECUERDA: Crea un archivo requirements.txt con: pandas, openpyxl, plotly, streamlit
st.title("📊 Análisis de Modulación por Periodos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

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

        # --- FILTROS DE TIEMPO ---
        opcion = st.selectbox(
            "Selecciona el periodo de análisis:",
            ["Últimos 7 días", "Mes Actual (Calendario)", "Promedio Mensual (Histórico)"]
        )

        ultima_fecha = df_base['Entrega'].max()
        
        if opcion == "Últimos 7 días":
            fecha_limite = (ultima_fecha - pd.Timedelta(days=7)).date()
            df_final = df_base[df_base['Fecha'] > fecha_limite]
            agrupar_por = 'Fecha'
            
        elif opcion == "Mes Actual (Calendario)":
            mes_actual = ultima_fecha.month
            anio_actual = ultima_fecha.year
            df_final = df_base[(df_base['Entrega'].dt.month == mes_actual) & 
                               (df_base['Entrega'].dt.year == anio_actual)]
            agrupar_por = 'Fecha'
            
        else: # Promedio Mensual
            df_final = df_base.copy()
            df_final['Periodo'] = df_base['Entrega'].dt.to_period('M').astype(str)
            agrupar_por = 'Periodo'

        # --- GENERACIÓN DE DATOS (Misma lógica de la tabla) ---
        resumen_df = df_final.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Total_Unicos': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        # Calculamos los porcentajes exactos
        resumen_df['% Modulados'] = (resumen_df['Modulados'] / resumen_df['Total_Unicos']) * 100
        resumen_df['% No Modulados'] = 100 - resumen_df['% Modulados']

        # Preparar para Plotly
        df_plot = resumen_df.melt(
            id_vars=[agrupar_por], 
            value_vars=['% Modulados', '% No Modulados'], 
            var_name='Estado', 
            value_name='Porcentaje'
        )

        # --- GRÁFICO ---
        st.markdown("---")
        
        # Paleta de amarillos: Modulados (Amarillo fuerte), No Modulados (Amarillo pálido)
        colores = ['#FFD700', '#FFF9C4']

        fig = px.bar(
            df_plot,
            x=agrupar_por,
            y='Porcentaje',
            color='Estado',
            title=f"Cumplimiento de Modulación: {opcion}",
            color_discrete_sequence=colores,
            text='Porcentaje'
        )

        # Configuración visual
        fig.update_traces(
            texttemplate='%{y:.1f}%', 
            textposition='inside',
            insidetextanchor='middle'
        )
        
        fig.update_layout(
            yaxis_title="Porcentaje (%)",
            xaxis_title="Tiempo",
            legend_title="Leyenda",
            barmode='stack',
            xaxis={'type': 'category'} if agrupar_por == 'Fecha' else {}
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
