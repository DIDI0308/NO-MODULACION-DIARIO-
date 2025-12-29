import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Reporte de modulación", layout="wide")

# --- ESTILO CSS PARA LA TABLA ---
# Esto fuerza a los encabezados a ser amarillos, texto negro y centrados
st.markdown("""
    <style>
    /* Estilo para los encabezados de la tabla */
    thead tr th {
        background-color: #FFD700 !important;
        color: black !important;
        text-align: center !important;
        font-weight: bold !important;
    }
    /* Estilo para centrar el contenido de las celdas */
    [data-testid="stDataFrame"] div[role="gridcell"] {
        text-align: center !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ADH MODULACIÓN CD EA")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos (Hoja específica)
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")
        
        # LIMPIEZA TOTAL DE COLUMNAS
        df.columns = df.columns.str.strip()

        # --- PROCESAMIENTO BASE ---
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

        # --- SECCIÓN 1: GRÁFICO DE MODULACIÓN ---
        st.markdown("### Evolución de Modulación")
        opcion_graf = st.selectbox(
            "Selecciona el periodo para el gráfico:",
            ["Últimos 7 días", "Mes Actual", "Histórico"]
        )

        ultima_fecha = df_base['Entrega'].max()
        
        if opcion_graf == "Últimos 7 días":
            df_g = df_base[df_base['Fecha'] > (ultima_fecha - pd.Timedelta(days=7)).date()]
            agrupar = 'Fecha'
        elif opcion_graf == "Mes Actual":
            df_g = df_base[(df_base['Entrega'].dt.month == ultima_fecha.month) & 
                           (df_base['Entrega'].dt.year == ultima_fecha.year)]
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

        fig = px.bar(resumen.sort_values(agrupar), x=agrupar, y='% Modulación', 
                     text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(yaxis=dict(range=[0, 115]), xaxis={'type': 'category'})
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 2: DIARIO NO MODULACIÓN ---
        st.markdown("---")
        st.header("DIARIO")
        st.subheader("NO MODULACIÓN")
        
        df_no_modulados = df_base[df_base['es_modulado'] == False].copy()

        if not df_no_modulados.empty:
            fechas_disponibles = sorted(df_no_modulados['Fecha'].unique(), reverse=True)
            fecha_sel = st.selectbox("Filtrar por fecha específica:", fechas_disponibles)

            df_final_clientes = df_no_modulados[df_no_modulados['Fecha'] == fecha_sel].copy()

            if 'Motivo' in df_final_clientes.columns:
                df_final_clientes['Motivo'] = df_final_clientes['Motivo'].astype(str).replace(['nan', 'None'], 'Sin Motivo')
            else:
                df_final_clientes['Motivo'] = "Columna no encontrada"

            resultado_tabla = df_final_clientes.drop_duplicates(subset=['Client'], keep='first')

            columnas_finales = ['Client', 'Cam', 'F.Pedido', 'Motivo']
            cols_ok = [c for c in columnas_finales if c in resultado_tabla.columns]

            st.write(f"Resultados encontrados para el día seleccionado: **{len(resultado_tabla)}**")
            
            # Usamos dataframe con el CSS inyectado arriba
            st.dataframe(
                resultado_tabla[cols_ok], 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("No se encontraron registros de Clientes No Modulados.")

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
