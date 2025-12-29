import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gráfico Modulación 3.30.8", layout="wide")

st.title("📈 Gráfico de Rendimiento de Modulación")
st.write("Visualización de cumplimiento (DPS 88) - Hoja 3.30.8")

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
            "Selecciona el periodo para el gráfico:",
            ["Últimos 7 días", "Mes Actual (Calendario)", "Promedio Mensual (Histórico)"]
        )

        ultima_fecha = df_base['Entrega'].max()
        
        if opcion == "Últimos 7 días":
            fecha_limite = (ultima_fecha - pd.Timedelta(days=7)).date()
            df_final = df_base[df_base['Fecha'] > fecha_limite]
            eje_x = 'Fecha'
            
        elif opcion == "Mes Actual (Calendario)":
            mes_actual = ultima_fecha.month
            anio_actual = ultima_fecha.year
            df_final = df_base[(df_base['Entrega'].dt.month == mes_actual) & 
                               (df_base['Entrega'].dt.year == anio_actual)]
            eje_x = 'Fecha'
            
        else: # Promedio Mensual
            df_final = df_base.copy()
            df_final['Periodo'] = df_base['Entrega'].dt.to_period('M').astype(str)
            eje_x = 'Periodo'

        # --- GENERACIÓN DE DATOS PARA EL GRÁFICO ---
        resumen = df_final.groupby(eje_x).apply(
            lambda x: pd.Series({
                'Total Concatenados': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        resumen['% Modulación'] = (resumen['Modulados'] / resumen['Total Concatenados']) * 100
        # Ordenar cronológicamente para el gráfico
        resumen = resumen.sort_values(by=eje_x)

        # --- VISUALIZACIÓN DEL GRÁFICO ---
        st.markdown("---")
        st.subheader(f"Evolución de % Modulación: {opcion}")

        # Preparamos los datos para el gráfico (Eje X: Fecha/Periodo, Eje Y: %)
        chart_data = resumen.set_index(eje_x)[['% Modulación']]
        
        # Mostramos el gráfico de barras
        st.bar_chart(chart_data)

        # También añadimos métricas clave debajo del gráfico para contexto
        col1, col2, col3 = st.columns(3)
        promedio_periodo = resumen['% Modulación'].mean()
        max_periodo = resumen['% Modulación'].max()
        
        col1.metric("Promedio del Periodo", f"{promedio_periodo:.2f}%")
        col2.metric("% Más Alto", f"{max_periodo:.2f}%")
        col3.metric("Días/Meses Evaluados", len(resumen))

    except Exception as e:
        st.error(f"Error al generar el gráfico. Verifique los datos del archivo.")
