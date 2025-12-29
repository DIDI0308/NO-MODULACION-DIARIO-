import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Modulación & Errores", layout="wide")

st.title("Análisis de Modulación y Reporte de Errores")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos (Hoja específica)
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")
        
        # --- LIMPIEZA TOTAL DE COLUMNAS ---
        # Quitamos espacios al inicio/final y aseguramos que "Motivo" se llame exactamente así
        df.columns = df.columns.str.strip()

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

        # --- SECCIÓN 1: GRÁFICO DE MODULACIÓN (TABLA OCULTA) ---
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

        resumen = df_g.groupby(agrupar).apply(lambda x: pd.Series({
            'Total': x['CONCATENADO'].nunique(),
            'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
        })).reset_index()
        resumen['% Modulación'] = (resumen['Modulados'] / resumen['Total']) * 100

        fig = px.bar(resumen.sort_values(agrupar), x=agrupar, y='% Modulación', text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(yaxis=dict(range=[0, 115]), xaxis={'type': 'category'})
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 2: TABLA DE ERRORES CON COLUMNA MOTIVO ---
        st.markdown("---")
        st.markdown("### ⚠️ Reporte de Registros con Error")
        
        # Filtramos Errores (BUSCA no válido)
        df_errores = df_base[df_base['es_modulado'] == False].copy()

        if not df_errores.empty:
            fechas_disponibles = sorted(df_errores['Fecha'].unique(), reverse=True)
            fecha_filtro = st.selectbox("Elige una fecha para ver los errores:", fechas_disponibles)

            # Filtro por fecha
            df_final_err = df_errores[df_errores['Fecha'] == fecha_filtro].copy()

            # Aseguramos que la columna 'Motivo' sea tratada como texto y no se oculte
            if 'Motivo' in df_final_err.columns:
                df_final_err['Motivo'] = df_final_err['Motivo'].astype(str).replace(['nan', 'None', ''], 'Sin Motivo especificado')
            else:
                # Si por alguna razón la columna no se mapeó, la creamos vacía para no romper el código
                df_final_err['Motivo'] = "Columna no encontrada"

            # REGLA: Sin repetidos por 'Client', solo el primero
            resultado_tabla = df_final_err.drop_duplicates(subset=['Client'], keep='first')

            # Columnas a mostrar (Estrictamente estas tres)
            columnas_visibles = ['Client', 'F.Pedido', 'Motivo']
            
            # Filtramos solo las que existen para seguridad
            cols_finales = [c for c in columnas_visibles if c in resultado_tabla.columns]

            st.write(f"Mostrando **{len(resultado_tabla)}** clientes únicos con error para el día **{fecha_filtro}**")
            
            # MOSTRAR TABLA
            st.dataframe(resultado_tabla[cols_finales], use_container_width=True, hide_index=True)
            
        else:
            st.success("No se encontraron errores en la columna BUSCA.")

    except Exception as e:
        st.error(f"Error crítico: {e}")
