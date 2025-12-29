import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Modulación & Errores", layout="wide")

st.title("📊 Análisis de Modulación y Reporte de Errores")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos (Hoja específica)
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO BASE ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha'] = df['Entrega'].dt.date
        
        # Filtro base permanente: Solo DPS 88
        df_base = df[df['DPS'].astype(str).str.contains('88')].copy()

        # Lógica de validación para columna BUSCA
        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "error" in str(valor).lower() or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        df_base['es_modulado'] = df_base['BUSCA'].apply(es_valido)

        # --- SECCIÓN 1: GRÁFICO DE MODULACIÓN ---
        st.markdown("### 📈 Evolución de Modulación")
        opcion_grafico = st.selectbox(
            "Selecciona el periodo para el gráfico:",
            ["Últimos 7 días", "Mes Actual (Calendario)", "Promedio Mensual (Histórico)"]
        )

        ultima_fecha = df_base['Entrega'].max()
        
        if opcion_grafico == "Últimos 7 días":
            fecha_limite = (ultima_fecha - pd.Timedelta(days=7)).date()
            df_graf = df_base[df_base['Fecha'] > fecha_limite]
            agrupar_por = 'Fecha'
        elif opcion_grafico == "Mes Actual (Calendario)":
            df_graf = df_base[(df_base['Entrega'].dt.month == ultima_fecha.month) & 
                              (df_base['Entrega'].dt.year == ultima_fecha.year)]
            agrupar_por = 'Fecha'
        else:
            df_graf = df_base.copy()
            df_graf['Periodo'] = df_base['Entrega'].dt.to_period('M').astype(str)
            agrupar_por = 'Periodo'

        # Cálculo de métricas para el gráfico
        resumen = df_graf.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Total': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()
        resumen['% Modulación'] = (resumen['Modulados'] / resumen['Total']) * 100

        # Mostrar gráfico de barras amarillas
        fig = px.bar(resumen.sort_values(agrupar_por), x=agrupar_por, y='% Modulación', 
                     text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(yaxis=dict(range=[0, 115]), xaxis={'type': 'category'})
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 2: TABLA DE ERRORES ---
        st.markdown("---")
        st.markdown("### ⚠️ Reporte de Registros con Error (BUSCA No Válido)")
        
        # Filtramos solo los que NO son modulados (Errores en BUSCA)
        df_errores = df_base[df_base['es_modulado'] == False].copy()

        if not df_errores.empty:
            # Selector visual de una fecha específica
            fechas_disponibles = sorted(df_errores['Fecha'].unique(), reverse=True)
            fecha_filtro = st.selectbox("Elige una fecha para ver los errores detallados:", fechas_disponibles)

            # Filtro por la fecha seleccionada
            df_error_fecha = df_errores[df_errores['Fecha'] == fecha_filtro].copy()

            # Columnas requeridas: Client, F.Pedido y Motivo (según tu imagen)
            col_motivo = "Motivo" 
            cols_deseadas = ['Client', 'F.Pedido', col_motivo]
            
            # Limpiar y asegurar que la columna Motivo sea visible
            if col_motivo in df_error_fecha.columns:
                df_error_fecha[col_motivo] = df_error_fecha[col_motivo].fillna("Sin información").astype(str)
            
            # Lógica: Sin repetidos según 'Client', manteniendo solo el primero
            resultado_final = df_error_fecha.drop_duplicates(subset=['Client'], keep='first')

            # Filtrar solo las columnas que existen en el DataFrame para evitar errores
            cols_finales = [c for c in cols_deseadas if c in resultado_final.columns]

            st.write(f"Se encontraron **{len(resultado_final)}** errores únicos de clientes para el día seleccionado.")
            
            # Mostrar la tabla final
            st.dataframe(resultado_final[cols_finales], use_container_width=True, hide_index=True)
        else:
            st.success("🎉 ¡Excelente! No se detectaron errores de búsqueda en este archivo.")

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
