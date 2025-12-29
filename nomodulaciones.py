import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Reporte de modulación", layout="wide")

st.title("ADH MODULACIÓN CD EA")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos (Hoja específica)
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")
        
        # LIMPIEZA TOTAL DE COLUMNAS (Espacios ocultos)
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
            # Filtro Mes Actual: Desde el día 1 del mes de la última fecha hasta el final disponible
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

        # --- SECCIÓN 2: CLIENTES ---
        st.markdown("---")
        st.header("DIARIO")
        st.subheader("NO MODULACIÓN")
        
        # Filtramos los NO modulados
        df_no_modulados = df_base[df_base['es_modulado'] == False].copy()

        if not df_no_modulados.empty:
            fechas_disponibles = sorted(df_no_modulados['Fecha'].unique(), reverse=True)
            fecha_sel = st.selectbox("Filtrar por fecha específica:", fechas_disponibles)

            df_final_clientes = df_no_modulados[df_no_modulados['Fecha'] == fecha_sel].copy()

            # Asegurar formato texto para Client y F.Pedido
            df_final_clientes['Client'] = df_final_clientes['Client'].astype(str)
            df_final_clientes['F.Pedido'] = df_final_clientes['F.Pedido'].astype(str)

            if 'Motivo' in df_final_clientes.columns:
                df_final_clientes['Motivo'] = df_final_clientes['Motivo'].astype(str).replace(['nan', 'None'], 'Sin Motivo')
            
            # Quitar repetidos por Client (solo el primero)
            resultado_tabla = df_final_clientes.drop_duplicates(subset=['Client'], keep='first')
            columnas_finales = ['Client', 'Cam', 'F.Pedido', 'Motivo']
            cols_ok = [c for c in columnas_finales if c in resultado_tabla.columns]

            # --- DISEÑO ESTÉTICO PERSONALIZADO (SIN BORDES) ---
            st.markdown("""
                <style>
                .main-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: Arial, sans-serif;
                    margin-top: 20px;
                }
                .main-table thead th {
                    background-color: #FFD700 !important;
                    color: black !important;
                    text-align: center !important;
                    padding: 12px;
                    font-weight: bold;
                    border: none !important;
                }
                .main-table tbody td {
                    text-align: center !important;
                    padding: 10px;
                    border: none !important;
                    border-bottom: 1px solid #EEEEEE !important; /* Línea sutil horizontal */
                }
                .main-table tbody tr:nth-child(even) {
                    background-color: #FAFAFA;
                }
                </style>
            """, unsafe_allow_html=True)

            # Generar HTML
            html_tabla = resultado_tabla[cols_ok].to_html(index=False, classes='main-table')
            
            st.write(f"Clientes encontrados: **{len(resultado_tabla)}**")
            st.markdown(html_tabla, unsafe_allow_html=True)
            
        else:
            st.warning("No se encontraron registros de No Modulación.")

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
