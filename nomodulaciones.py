import streamlit as st
import pandas as pd
import plotly.express as px 

# Configuración de página
st.set_page_config(page_title="Reporte de modulación", layout="wide")

# --- DEFINICIÓN DE ICONOS SVG (PATHS) ---
SVG_PERSONA = "M256 0c70.7 0 128 57.3 128 128s-57.3 128-128 128S0 198.7 0 128 57.3 0 128 0zm0 304c118.6 0 222.5 58.5 269.3 143 7.9 14.2 1.7 32.1-13.7 39.7-6.9 3.4-14.5 5.1-22 5.1-8.1 0-16.3-2-23.6-6.1-34.8-19.7-74.8-30.7-117-30.7-41.8 0-81.4 10.8-116.2 30.3-14.8 8.3-33.7 2.9-42.2-11.7-8.4-14.6-3.4-33.6 11.3-42.1C112.6 347.1 181.7 304 256 304z"
SVG_CAMION = "M624 352h-16V243.9c0-12.7-5.1-24.9-14.1-33.9L494 110.1c-9-9-21.2-14.1-33.9-14.1H416V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48v320c0 26.5 21.5 48 48 48h16c0 53 43 96 96 96s96-43 96-96h128c0 53 43 96 96 96s96-43 96-96h48c26.5 0 48-21.5 48-48v-64c0-26.5-21.5-48-48-48zm-16-224h-64V64h64v64zm48 224c-26.5 0-48 21.5-48 48s21.5 48 48 48 48-21.5 48-48-21.5-48-48-48zm-496 0c-26.5 0-48 21.5-48 48s21.5 48 48 48 48-21.5 48-48-21.5-48-48-48zm368 0H192v-32h272v32z"

# --- INYECCIÓN DE CSS (ESTILOS VISUALES) ---
st.markdown("""
    <style>
    /* 1. Fondo Global Negro */
    .stApp { background-color: #000000; }

    /* 2. Textos en AMARILLO */
    h1, h2, h3, h4, h5, .stMarkdown h3 { color: #FFD700 !important; }
    .stSelectbox label, .stFileUploader label, p { color: #FFD700 !important; font-weight: bold; }

    /* 3. BOTONES Y FILTROS */
    div.stButton > button { background-color: #FFD700 !important; color: black !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; }
    div[data-baseweb="select"] > div { background-color: #FFD700 !important; color: black !important; border-radius: 8px !important; border: 1px solid white !important; }
    div[data-baseweb="select"] div, div[data-baseweb="select"] span, div[data-baseweb="select"] svg { color: black !important; fill: black !important; }

    /* 4. CONTENEDORES BLANCOS (Tablas y Gráficas) */
    .white-card-container {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(255, 215, 0, 0.1);
        color: black !important;
    }

    /* Estilos de Tabla */
    .tabla-final { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; color: black !important; }
    .tabla-final thead th { background-color: #FFD700 !important; color: black !important; text-align: center !important; padding: 12px !important; border-top-left-radius: 10px; border-top-right-radius: 10px; }
    .tabla-final tbody td { background-color: white !important; color: black !important; text-align: center !important; padding: 10px !important; border-bottom: 1px solid #eee !important; }

    /* Estilos para Plotly estándar */
    div[data-testid="stPlotlyChart"] { background-color: white; border-radius: 20px; overflow: hidden; padding: 10px; box-shadow: 0 4px 8px rgba(255, 215, 0, 0.1); }

    /* --- NUEVOS ESTILOS PARA LOS ISOTIPOS --- */
    .isotype-row {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }
    .isotype-label {
        flex: 0 0 100px;
        font-weight: bold;
        color: black;
        font-size: 1.1em;
    }
    .icon-wrapper {
        position: relative;
        width: 60px;
        height: 60px;
        margin-right: 20px;
    }
    .icon-bg {
        position: absolute;
        top: 0; left: 0;
        width: 60px; height: 60px;
        fill: #e0e0e0; /* Gris fondo */
    }
    .icon-fill-container {
        position: absolute;
        top: 0; left: 0;
        height: 60px;
        overflow: hidden; /* Recorte mágico */
        z-index: 10;
    }
    .icon-fg {
        position: absolute;
        top: 0; left: 0;
        width: 60px; height: 60px; /* Mismo tamaño que wrapper */
        fill: #FFD700; /* Amarillo */
    }
    .isotype-value {
        font-weight: bold;
        color: black;
        font-size: 1.5em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN GENERADORA DE HTML ---
def generar_html_isotipo(df_top, col_id, col_valor, svg_path, viewBox_cfg):
    if df_top.empty:
        return "<div class='white-card-container'>No hay datos.</div>"
    
    max_valor = df_top[col_valor].max()
    
    # Inicio del contenedor blanco
    html_output = "<div class='white-card-container'>"
    
    for index, row in df_top.iterrows():
        codigo = row[col_id]
        valor = row[col_valor]
        porcentaje = (valor / max_valor * 100) if max_valor > 0 else 0
        
        # HTML de cada fila
        html_output += f"""
        <div class="isotype-row">
            <div class="isotype-label">{codigo}</div>
            
            <div class="icon-wrapper">
                <svg class="icon-bg" viewBox="{viewBox_cfg}" xmlns="http://www.w3.org/2000/svg">
                    <path d="{svg_path}"/>
                </svg>
                
                <div class="icon-fill-container" style="width: {porcentaje}%;">
                    <svg class="icon-fg" viewBox="{viewBox_cfg}" xmlns="http://www.w3.org/2000/svg">
                        <path d="{svg_path}"/>
                    </svg>
                </div>
            </div>
            
            <div class="isotype-value">{valor}</div>
        </div>
        """
    
    html_output += "</div>" # Cierre contenedor blanco
    return html_output

# ==============================================================================
# APP PRINCIPAL
# ==============================================================================

st.title("ADH MODULACIÓN CD EA")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # --- CARGA DATOS ---
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
        # SECCIÓN 2: CLIENTES NO MODULADOS
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
            <div class="white-card-container">
                <h4 style="color:black !important; margin-top:0;">Clientes encontrados: {len(resultado)}</h4>
                {resultado[cols].to_html(index=False, classes='tabla-final')}
            </div>
            """
            st.markdown(html_tabla, unsafe_allow_html=True)
        else:
            st.warning("No hay datos para Clientes No Modulados.")

        # ==========================================
        # SECCIÓN 3: REINCIDENCIAS CLIENTES (ISOTIPO)
        # ==========================================
        st.markdown("---")
        st.header("REINCIDENCIAS - CLIENTES")
        st.subheader("Top 10 Clientes más reincidentes (Días únicos)")

        if not df_no_mod.empty:
            col_filt_re, col_blank = st.columns([1, 3])
            with col_filt_re:
                opcion_reinc = st.selectbox("Periodo Clientes:", ["Últimos 7 días", "Mes Actual", "Último Año"], key="opt_reinc_client")
            
            df_re = df_no_mod.copy()
            df_re['Client'] = df_re['Client'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))
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
                
                # --- RENDERIZADO HTML ---
                html_clientes = generar_html_isotipo(top, 'Client', 'Cantidad', SVG_PERSONA, "0 0 512 512")
                st.markdown(html_clientes, unsafe_allow_html=True) # IMPORTANTE: unsafe_allow_html=True
                
            else:
                st.info("No se encontraron datos.")

        # ==========================================
        # SECCIÓN 4: REINCIDENCIAS CAMIONES (ISOTIPO)
        # ==========================================
        st.markdown("---")
        st.header("REINCIDENCIAS - CAMIONES")
        st.subheader("Top 10 Camiones con más incidencias (Días únicos)")

        if not df_no_mod.empty:
            col_filt_cam, col_blank_cam = st.columns([1, 3])
            with col_filt_cam:
                opcion_cam = st.selectbox("Periodo Camiones:", ["Últimos 7 días", "Mes Actual", "Último Año"], key="opt_reinc_cam")
            
            df_cam = df_no_mod.copy()
            if 'Cam' in df_cam.columns:
                df_cam['Cam'] = df_cam['Cam'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))
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

                    # --- RENDERIZADO HTML ---
                    html_camiones = generar_html_isotipo(top_cam, 'Cam', 'Cantidad', SVG_CAMION, "0 0 640 512")
                    st.markdown(html_camiones, unsafe_allow_html=True) # IMPORTANTE: unsafe_allow_html=True
                    
                else:
                    st.info("No se encontraron reincidencias de camiones.")
            else:
                st.error("No se encontró la columna 'Cam' en el archivo.")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
