import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Modulación 3.30.8", layout="wide")

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

        # --- GENERACIÓN DE DATOS PARA EL GRÁFICO ---
        resumen_df = df_final.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique(),
                'No Modulados': x[~x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        # Convertir a formato largo para Plotly (Melt)
        df_plot = resumen_df.melt(id_vars=[agrupar_por], value_vars=['Modulados', 'No Modulados'], 
                                   var_name='Estado', value_name='Cantidad')

        # --- GRÁFICO ---
        st.markdown("---")
        
        # Paleta de amarillos
        colores_amarillos = ['#FFD700', '#FFFACD'] # Oro para Modulados, Amarillo claro para No Modulados

        fig = px.bar(
            df_plot,
            x=agrupar_por,
            y='Cantidad',
            color='Estado',
            title=f"Distribución de Modulación: {opcion}",
            color_discrete_sequence=colores_amarillos,
            barmode='relative', # Esto permite el apilado
            text='Cantidad'
        )

        # Configuración para que sea 100% apilado
        fig.update_layout(barnorm='percent')
        
        # Etiquetas de datos en porcentaje
        fig.update_traces(texttemplate='%{y:.1f}%', textposition='inside')
        
        # Mejorar estética de ejes
        fig.update_layout(
            yaxis_title="Porcentaje (%)",
            xaxis_title="Fecha / Periodo",
            legend_title="Estado",
            uniformtext_minsize=8, 
            uniformtext_mode='hide'
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
