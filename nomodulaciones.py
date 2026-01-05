import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Reporte de modulación", layout="wide")

# --- INYECCIÓN DE CSS (ESTILOS VISUALES) ---
st.markdown("""
    <style>
    /* 1. Fondo Global Negro */
    .stApp {
        background-color: #000000;
    }

    /* 2. Textos Generales: Títulos y Subtítulos en AMARILLO */
    h1, h2, h3, h4, h5, .stMarkdown h3 {
        color: #FFD700 !important;
    }
    
    /* 3. Estilo de Etiquetas (Labels) */
    .stSelectbox label, .stFileUploader label, p {
        color: #FFD700 !important;
        font-weight: bold;
    }

    /* 4. BOTONES Y FILTROS (Amarillo con Texto Negro) */
    
    /* Botones generales (incluye el de subir archivo) */
    div.stButton > button {
        background-color: #FFD700 !important;
        color: black !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }

    /* Caja de selección (Selectbox - Input principal) */
    div[data-baseweb="select"] > div {
        background-color: #FFD700 !important;
        color: black !important;
        border-radius: 8px !important;
        border: 1px solid white !important;
    }
    
    /* Texto dentro del Selectbox */
    div[data-baseweb="select"] div, 
    div[data-baseweb="select"] span, 
    div[data-baseweb="select"] svg {
        color: black !important;
        fill: black !important; /* Para la flechita */
    }

    /* 5. Estilo de la Tabla (Dentro de tarjeta blanca redondeada) */
    .tabla-container {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(255, 215, 0, 0.1);
    }
    
    .tabla-final {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        color: black !important;
    }
    .tabla-final thead th {
        background-color: #FFD700 !important;
        color: black !important;
        text-align: center !important;
        padding: 12px !important;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }
    .tabla-final tbody td {
        background-color: white !important;
        color: black !important;
        text-align: center !important;
        padding: 10px !important;
        border-bottom: 1px solid #eee !important;
    }

    /* 6. Estilo para redondear el contenedor de las gráficas Plotly */
    div[data-testid="stPlotlyChart"] {
        background-color: white;
        border-radius: 20px;
        overflow: hidden;
        padding: 10px;
        box-shadow: 0 4px 8px rgba(255, 215, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ADH MODULACIÓN CD EA")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # --- CARGA Y PROCESAMIENTO ---
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")
        df.columns = df.columns.str.strip()

        df['Entrega'] = pd.to_datetime(df['Entrega'], errors='coerce')
        df = df.dropna(subset=['Entrega'])
        df['Fecha'] = df['Entrega'].dt.date
        
        # Filtro DPS 88
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
        ultima_fecha = df_base['Entrega'].max()

        # ==========================================
        # SECCIÓN 1: GRÁFICO EVOLUCIÓN
        # ==========================================
        st.markdown("### Evolución de Modulación")
        opcion_graf = st.selectbox("Selecciona el periodo:", ["Últimos 7 días", "Mes Actual", "Histórico"], key="opt_evol")
        
        if opcion_graf == "Últimos 7 días":
            df_g = df_base[df_base['Fecha'] > (ultima_fecha - pd.Timedelta(days=7)).date()]
        elif opcion_graf == "Mes Actual":
            df_g = df_base[(df_base['Entrega'].dt.month == ultima_fecha.month) & (df_base['Entrega'].dt.year == ultima_fecha.year)]
        else:
            df_g = df_base.copy()

        agrupar = 'Fecha' if opcion_graf != "Histórico" else df_g['Entrega'].dt.to_period('M').astype(str)
        resumen = df_g.groupby(agrupar).apply(
            lambda x: pd.Series({'% Modulación': (x[x['es_modulado']]['CONCATENADO'].nunique() / x['CONCATENADO'].nunique()) * 100})
        ).reset_index()

        fig = px.bar(resumen, x=resumen.columns[0], y='% Modulación', text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        
        fig.update_layout(
            paper_bgcolor='white', plot_bgcolor='white', font={'color': 'black'},
            margin=dict(t=50, l=50, r=50, b=50),
            xaxis_title="Fecha / Periodo", yaxis_title="% Modulación",
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # SECCIÓN 2: CLIENTES NO MODULADOS (TABLA)
        # ==========================================
        st.markdown("---")
        st.header("DIARIO - NO MODULACIÓN")
        
        df_no_mod = df_base[df_base['es_modulado'] == False].copy()

        if not df_no_mod.empty:
            fecha_sel = st.selectbox("Filtrar por fecha:", sorted(df_no_mod['Fecha'].unique(), reverse=True), key="opt_fecha")
            df_f = df_no_mod[df_no_mod['Fecha'] == fecha_sel].copy()

            for col in ['Client', 'F.Pedido']:
                if col in df_f.columns:
                    df_f[col] = df_f[col].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))
            
            if 'Motivo' in df_f.columns:
                df_f['Motivo'] = df_f['Motivo'].astype(str).replace(['nan', 'None'], 'Sin Motivo')

            resultado = df_f.drop_duplicates(subset=['Client'], keep='first')
            cols = [c for c in ['Client', 'Cam', 'F.Pedido', 'Motivo'] if c in resultado.columns]

            html_tabla = f"""
            <div class="tabla-container">
                <h4 style="color:black !important; margin-top:0;">Clientes encontrados: {len(resultado)}</h4>
                {resultado[cols].to_html(index=False, classes='tabla-final')}
            </div>
            """
            st.markdown(html_tabla, unsafe_allow_html=True)
        else:
            st.warning("No hay datos para Clientes No Modulados.")

        # ==========================================
        # SECCIÓN 3: REINCIDENCIAS CLIENTES
        # ==========================================
        st.markdown("---")
        st.header("REINCIDENCIAS")
        st.subheader("Top 10 Clientes más reincidentes")

        if not df_no_mod.empty:
            col_filt_re, col_blank = st.columns([1, 3])
            with col_filt_re:
                opcion_reinc = st.selectbox("Periodo Clientes:", ["Últimos 7 días", "Mes Actual", "Último Año"], key="opt_reinc_client")
            
            df_re = df_no_mod.copy()
            df_re['Client'] = df_re['Client'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))
            
            # Unicidad por día
            df_re_unicos = df_re.drop_duplicates(subset=['Client', 'Fecha'])

            if opcion_reinc == "Últimos 7 días":
                limite = ultima_fecha - pd.Timedelta(days=7)
                df_filt = df_re_unicos[df_re_unicos['Entrega'] > limite]
            elif opcion_reinc == "Mes Actual":
                df_filt = df_re_unicos[(df_re_unicos['Entrega'].dt.month == ultima_fecha.month) & (df_re_unicos['Entrega'].dt.year == ultima_fecha.year)]
            else:
                limite = ultima_fecha - pd.DateOffset(years=1)
                df_filt = df_re_unicos[df_re_unicos['Entrega'] > limite]

            if not df_filt.empty:
                top = df_filt['Client'].value_counts().reset_index()
                top.columns = ['Client', 'Cantidad']
                top = top.sort_values(by='Cantidad', ascending=False).head(10)

                fig_re = px.bar(top, x='Client', y='Cantidad', text='Cantidad', title=f"Top 10 Clientes ({opcion_reinc})", color_discrete_sequence=['#FFD700'])
                
                max_val = top['Cantidad'].max()
                limite_sup = 10 if max_val <= 10 else (max_val + 1)

                fig_re.update_layout(
                    paper_bgcolor='white', plot_bgcolor='white', font={'color': 'black'},
                    margin=dict(t=50, l=50, r=50, b=50),
                    xaxis_title="Código Cliente", yaxis_title="Días con Incidencia",
                    xaxis=dict(type='category', showgrid=False),
                    yaxis=dict(range=[0, limite_sup], dtick=1, showgrid=False)
                )
                fig_re.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig_re, use_container_width=True)
            else:
                st.info("No se encontraron datos.")

        # ==========================================
        # SECCIÓN 4: REINCIDENCIAS CAMIONES (NUEVO)
        # ==========================================
        st.markdown("---")
        st.subheader("Top 10 Camiones con más incidencias")

        if not df_no_mod.empty:
            col_filt_cam, col_blank_cam = st.columns([1, 3])
            with col_filt_cam:
                opcion_cam = st.selectbox("Periodo Camiones:", ["Últimos 7 días", "Mes Actual", "Último Año"], key="opt_reinc_cam")
            
            df_cam = df_no_mod.copy()
            # Limpieza columna Cam
            if 'Cam' in df_cam.columns:
                df_cam['Cam'] = df_cam['Cam'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))
                
                # Unicidad por día (Camión + Fecha)
                df_cam_unicos = df_cam.drop_duplicates(subset=['Cam', 'Fecha'])

                if opcion_cam == "Últimos 7 días":
                    limite = ultima_fecha - pd.Timedelta(days=7)
                    df_filt_cam = df_cam_unicos[df_cam_unicos['Entrega'] > limite]
                elif opcion_cam == "Mes Actual":
                    df_filt_cam = df_cam_unicos[(df_cam_unicos['Entrega'].dt.month == ultima_fecha.month) & (df_cam_unicos['Entrega'].dt.year == ultima_fecha.year)]
                else:
                    limite = ultima_fecha - pd.DateOffset(years=1)
                    df_filt_cam = df_cam_unicos[df_cam_unicos['Entrega'] > limite]

                if not df_filt_cam.empty:
                    top_cam = df_filt_cam['Cam'].value_counts().reset_index()
                    top_cam.columns = ['Cam', 'Cantidad']
                    top_cam = top_cam.sort_values(by='Cantidad', ascending=False).head(10)

                    fig_cam = px.bar(top_cam, x='Cam', y='Cantidad', text='Cantidad', title=f"Top 10 Camiones ({opcion_cam})", color_discrete_sequence=['#FFD700'])
                    
                    max_val_cam = top_cam['Cantidad'].max()
                    limite_sup_cam = 10 if max_val_cam <= 10 else (max_val_cam + 1)

                    fig_cam.update_layout(
                        paper_bgcolor='white', plot_bgcolor='white', font={'color': 'black'},
                        margin=dict(t=50, l=50, r=50, b=50),
                        xaxis_title="Código Camión", yaxis_title="Días con Incidencia",
                        xaxis=dict(type='category', showgrid=False),
                        yaxis=dict(range=[0, limite_sup_cam], dtick=1, showgrid=False)
                    )
                    fig_cam.update_traces(texttemplate='%{text}', textposition='outside')
                    st.plotly_chart(fig_cam, use_container_width=True)
                else:
                    st.info("No se encontraron reincidencias de camiones en el periodo seleccionado.")
            else:
                st.error("No se encontró la columna 'Cam' en el archivo.")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
