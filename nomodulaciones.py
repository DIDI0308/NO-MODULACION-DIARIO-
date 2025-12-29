import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Reporte de modulación", layout="wide")

# --- INYECCIÓN DE CSS GLOBAL PARA EL FORMATO DE LA TABLA ---
st.markdown("""
    <style>
    .tabla-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 20px;
    }
    .tabla-final {
        width: 100%;
        border-collapse: collapse;
        border: 2px solid white !important; /* Bordes exteriores blancos */
        font-family: Arial, sans-serif;
    }
    .tabla-final thead th {
        background-color: #FFD700 !important; /* Amarillo */
        color: black !important; /* Texto Negro */
        text-align: center !important;
        padding: 12px !important;
        border: 2px solid white !important; /* Bordes internos blancos */
        font-weight: bold;
    }
    .tabla-final tbody td {
        background-color: #F8F9FA !important;
        color: black !important;
        text-align: center !important;
        padding: 10px !important;
        border: 2px solid white !important; /* Bordes internos blancos */
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ADH MODULACIÓN CD EA")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")
        df.columns = df.columns.str.strip()

        # --- PROCESAMIENTO BASE ---
        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha'] = df['Entrega'].dt.date
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

        # --- SECCIÓN 1: GRÁFICO ---
        st.markdown("### Evolución de Modulación")
        opcion_graf = st.selectbox("Selecciona el periodo:", ["Últimos 7 días", "Mes Actual", "Histórico"])
        ultima_fecha = df_base['Entrega'].max()
        
        if opcion_graf == "Últimos 7 días":
            df_g = df_base[df_base['Fecha'] > (ultima_fecha - pd.Timedelta(days=7)).date()]
        elif opcion_graf == "Mes Actual":
            df_g = df_base[(df_base['Entrega'].dt.month == ultima_fecha.month) & (df_base['Entrega'].dt.year == ultima_fecha.year)]
        else:
            df_g = df_base.copy()

        # Agrupar para gráfico
        resumen = df_g.groupby('Fecha' if opcion_graf != "Histórico" else df_g['Entrega'].dt.to_period('M').astype(str)).apply(
            lambda x: pd.Series({'% Modulación': (x[x['es_modulado']]['CONCATENADO'].nunique() / x['CONCATENADO'].nunique()) * 100})
        ).reset_index()

        fig = px.bar(resumen, x=resumen.columns[0], y='% Modulación', text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 2: CLIENTES NO MODULADOS ---
        st.markdown("---")
        st.header("DIARIO")
        st.subheader("NO MODULACIÓN")
        
        df_no_mod = df_base[df_base['es_modulado'] == False].copy()

        if not df_no_mod.empty:
            fecha_sel = st.selectbox("Filtrar por fecha:", sorted(df_no_mod['Fecha'].unique(), reverse=True))
            df_f = df_no_mod[df_no_mod['Fecha'] == fecha_sel].copy()

            # --- CONVERSIÓN CRÍTICA A TEXTO ---
            # Forzamos que estas columnas sean tratadas como texto puro
            df_f['Client'] = df_f['Client'].astype(str)
            df_f['F.Pedido'] = df_f['F.Pedido'].astype(str)
            
            if 'Motivo' in df_f.columns:
                df_f['Motivo'] = df_f['Motivo'].astype(str).replace(['nan', 'None'], 'Sin Motivo')

            # Eliminar duplicados por Client
            resultado = df_f.drop_duplicates(subset=['Client'], keep='first')
            
            # Columnas requeridas
            cols = [c for c in ['Client', 'Cam', 'F.Pedido', 'Motivo'] if c in resultado.columns]

            # Renderizado de la tabla con la clase CSS personalizada
            html_tabla = resultado[cols].to_html(index=False, classes='tabla-final')
            
            st.write(f"Clientes encontrados: **{len(resultado)}**")
            st.markdown(f'<div class="tabla-container">{html_tabla}</div>', unsafe_allow_html=True)
            
        else:
            st.warning("No hay datos para Clientes No Modulados.")

    except Exception as e:
        st.error(f"Error en el proceso: {e}")
