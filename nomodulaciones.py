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

        # --- FILTROS DE TIEMPO (Selector principal) ---
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

        # --- GENERACIÓN DE DATOS ---
        resumen = df_final.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Total Concatenados': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        resumen['% Modulación'] = (resumen['Modulados'] / resumen['Total Concatenados']) * 100
        
        # Ordenar para que el gráfico fluya cronológicamente (de izquierda a derecha)
        resumen_grafico = resumen.sort_values(by=agrupar_por, ascending=True)

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        
        # 1. Gráfico de Barras
        st.subheader(f"Gráfico: % Modulación ({opcion})")
        
        fig = px.bar(
            resumen_grafico,
            x=agrupar_por,
            y='% Modulación',
            color_discrete_sequence=['#FFD700'], # Color Amarillo
            text='% Modulación'
        )

        fig.update_traces(
            texttemplate='%{y:.1f}%', 
            textposition='outside'
        )

        fig.update_layout(
            yaxis_title="% Modulación",
            xaxis_title="Día / Periodo",
            yaxis=dict(range=[0, 115]), # Espacio para las etiquetas
            xaxis={'type': 'category'}  # Evita huecos en fechas vacías
        )

        st.plotly_chart(fig, use_container_width=True)

        # 2. Tabla Detallada (debajo del gráfico)
        st.markdown("---")
        st.subheader("Datos Detallados")
        
        # Re-ordenar para la tabla (más reciente primero)
        resumen_tabla = resumen.sort_values(by=agrupar_por, ascending=False)
        
        formatos = {
            'Total Concatenados': '{:,.0f}',
            'Modulados': '{:,.0f}',
            '% Modulación': '{:.2f}%'
        }
        
        if agrupar_por == 'Fecha':
            formatos['Fecha'] = lambda x: x.strftime('%d/%m/%Y')
        else:
            formatos['Periodo'] = lambda x: str(x)

        st.dataframe(
            resumen_tabla.style.format(formatos), 
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:
        st.error(f"Error al procesar el archivo.")
