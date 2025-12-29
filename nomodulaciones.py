import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.colors as mcolors

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

        # Fecha de referencia (la más reciente en el archivo)
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
            df_final['Periodo'] = df_base['Entrega'].dt.to_period('M')
            agrupar_por = 'Periodo'

        # --- GENERACIÓN DE DATOS PARA EL GRÁFICO ---
        resumen_df = df_final.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Total Concatenados': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        # Evitar división por cero
        resumen_df['No Modulados'] = resumen_df['Total Concatenados'] - resumen_df['Modulados']
        resumen_df['% Modulación'] = (resumen_df['Modulados'] / resumen_df['Total Concatenados']) * 100
        resumen_df['% No Modulación'] = (resumen_df['No Modulados'] / resumen_df['Total Concatenados']) * 100

        # Ordenar por fecha o periodo
        resumen_df = resumen_df.sort_values(by=agrupar_por, ascending=True)

        # Preparar los datos para el gráfico apilado
        # Melting the DataFrame to get a 'value' column for stacking
        df_melted = resumen_df.melt(id_vars=[agrupar_por], value_vars=['% Modulación', '% No Modulación'], 
                                    var_name='Tipo de Modulación', value_name='Porcentaje')

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        st.subheader(f"Gráfico de Modulación: {opcion}")
        
        # Paleta de colores amarillos (ejemplo de amarillos a naranjas)
        # Puedes ajustar los colores HEX si tienes unos específicos
        yellow_palette = ["#FFFF00", "#FFD700", "#FFA500", "#FF8C00"]
        
        # Crear el gráfico de barras apiladas al 100%
        fig = px.bar(
            df_melted,
            x=agrupar_por,
            y='Porcentaje',
            color='Tipo de Modulación',
            text_auto='.2s',  # Formato automático de texto, 2 decimales
            title=f'Porcentaje de Modulación vs No Modulación por {agrupar_por}',
            labels={'Porcentaje': 'Porcentaje (%)', agrupar_por: 'Periodo'},
            color_discrete_sequence=yellow_palette, # Aplica la paleta amarilla
            height=500
        )

        # Ajustar el texto de las etiquetas para que sean %
        fig.update_traces(texttemplate='%{y:.2f}%', textposition='inside')
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

        # Asegurarse de que el eje Y vaya de 0 a 100
        fig.update_yaxes(range=[0, 100])

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo o generar el gráfico. Verifica el formato de tus datos y la existencia de las columnas requeridas.")
        st.exception(e) # Muestra el detalle del error para depuración
