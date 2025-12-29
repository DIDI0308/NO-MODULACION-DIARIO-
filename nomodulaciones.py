import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Modulación 3.30.8", layout="wide")

st.title("📊 Gráfico de % Modulación")
st.write("Cálculo: (Únicos Modulados / Únicos Totales de Concatenado) x 100")

# --- RECORDATORIO REQUERIMIENTOS ---
# Crea un archivo 'requirements.txt' en tu repo con:
# pandas
# openpyxl
# plotly
# streamlit

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar la hoja específica
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- LIMPIEZA Y PROCESAMIENTO ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha'] = df['Entrega'].dt.date
        
        # Filtro permanente: Solo DPS 88
        df_base = df[df['DPS'].astype(str).str.contains('88')].copy()

        # Función para validar la columna BUSCA
        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "error" in str(valor).lower() or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        df_base['es_modulado'] = df_base['BUSCA'].apply(es_valido)

        # --- SELECTOR DE PERIODO ---
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

        # --- CÁLCULO DE LA MÉTRICA ---
        resumen_df = df_final.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Total_Concatenados': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        # Cálculo exacto prevaleciente
        resumen_df['Porcentaje'] = (resumen_df['Modulados'] / resumen_df['Total_Concatenados']) * 100
        
        # Ordenar cronológicamente
        resumen_df = resumen_df.sort_values(by=agrupar_por)

        # --- GRÁFICO DE BARRAS SIMPLES ---
        st.markdown("---")
        
        fig = px.bar(
            resumen_df,
            x=agrupar_por,
            y='Porcentaje',
            title=f"Evolución de Modulación (%): {opcion}",
            text='Porcentaje',
            color_discrete_sequence=['#FFD700'] # Color Amarillo sólido
        )

        # Ajuste de etiquetas de datos y formato
        fig.update_traces(
            texttemplate='%{y:.1f}%', 
            textposition='outside' # Etiquetas arriba de las barras
        )
        
        fig.update_layout(
            yaxis_title="% Modulación",
            xaxis_title="Día / Periodo",
            yaxis=dict(range=[0, 115]), # Margen para que no se corten las etiquetas
            xaxis={'type': 'category'} # Evita que Plotly rellene huecos de fechas vacías
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo. Revisa que las columnas 'Entrega', 'DPS', 'CONCATENADO' y 'BUSCA' existan.")
