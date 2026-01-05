import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Reporte de modulación", layout="wide")

# --- INYECCIÓN DE CSS (DISEÑO NEGRO Y TARJETAS BLANCAS) ---
st.markdown("""
    <style>
    /* 1. Fondo Global Negro */
    .stApp {
        background-color: #000000;
        color: white;
    }

    /* 2. Estilo para los Títulos Principales (H1, H2) en Blanco */
    h1, h2, h3 {
        color: white !important;
    }

    /* 3. Estilo de la Tabla Final (Dentro de tarjeta blanca) */
    .tabla-container {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .tabla-final {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        color: black !important;
    }
    .tabla-final thead th {
        background-color: #FFD700 !important; /* Amarillo */
        color: black !important;
        text-align: center !important;
        padding: 12px !important;
        border-bottom: 2px solid #ddd !important;
    }
    .tabla-final tbody td {
        background-color: white !important;
        color: black !important;
        text-align: center !important;
        padding: 10px !important;
        border-bottom: 1px solid #eee !important;
    }

    /* 4. Ajustes para Widgets (Selectbox) para que se vean bien en negro */
    .stSelectbox label {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ADH MODULACIÓN CD EA")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # --- CARGA Y PROCESAMIENTO (Igual que antes) ---
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

        # ==========================================
        # SECCIÓN 1: GRÁFICO EVOLUCIÓN (CARD BLANCA)
        # ==========================================
        st.markdown("### Evolución de Modulación")
        opcion_graf = st.selectbox("Selecciona el periodo:", ["Últimos 7 días", "Mes Actual", "Histórico"], key="opt_evol")
        
        ultima_fecha = df_base['Entrega'].max()
        
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

        # Gráfico con fondo blanco (Card effect)
        fig = px.bar(resumen, x=resumen.columns[0], y='% Modulación', text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        
        # AQUI SE CONFIGURA EL "RECUADRO BLANCO" DE LA GRAFICA
        fig.update_layout(
            paper_bgcolor='white',   # Fondo exterior blanco
            plot_bgcolor='white',    # Fondo de las barras blanco
            font={'color': 'black'}, # Texto negro
            margin=dict(t=50, l=50, r=50, b=50), # Margen interno
            xaxis_title="Fecha / Periodo",
            yaxis_title="% Modulación"
        )
        st.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # SECCIÓN 2: CLIENTES NO MODULADOS (CARD BLANCA)
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

            # Render HTML dentro de un div blanco para simular la "Card"
            html_tabla = f"""
            <div class="tabla-container">
                <h4 style="color:black; margin-top:0;">Clientes encontrados: {len(resultado)}</h4>
                {resultado[cols].to_html(index=False, classes='tabla-final')}
            </div>
            """
            st.markdown(html_tabla, unsafe_allow_html=True)
            
        else:
            st.warning("No hay datos para Clientes No Modulados.")

        # ==========================================
        # SECCIÓN 3: REINCIDENCIAS (CARD BLANCA + EJE Y 0-10)
        # ==========================================
        st.markdown("---")
        st.header("REINCIDENCIAS")
        st.subheader("Top 10 Clientes más reincidentes (Días únicos)")

        if not df_no_mod.empty:
            col_filt_re, col_blank = st.columns([1, 3])
            with col_filt_re:
                opcion_reincidencia = st.selectbox("Periodo Reincidencia:", ["Últimos 7 días", "Mes Actual", "Último Año"], key="opt_reinc")
            
            df_re = df_no_mod.copy()
            df_re['Client'] = df_re['Client'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))
            
            # 1. Eliminar duplicados de fecha por cliente (1 error por día máx)
            df_re_unicos = df_re.drop_duplicates(subset=['Client', 'Fecha'])

            top_clientes = pd.DataFrame()

            if opcion_reincidencia == "Últimos 7 días":
                fecha_limite = ultima_fecha - pd.Timedelta(days=7)
                df_re_filt = df_re_unicos[df_re_unicos['Entrega'] > fecha_limite]
                
            elif opcion_reincidencia == "Mes Actual":
                df_re_filt = df_re_unicos[
                    (df_re_unicos['Entrega'].dt.month == ultima_fecha.month) & 
                    (df_re_unicos['Entrega'].dt.year == ultima_fecha.year)
                ]
                
            else: # Último Año
                fecha_limite = ultima_fecha - pd.DateOffset(years=1)
                df_re_filt = df_re_unicos[df_re_unicos['Entrega'] > fecha_limite]

            if not df_re_filt.empty:
                # Conteo total (Suma de incidencias únicas)
                top_clientes = df_re_filt['Client'].value_counts().reset_index()
                top_clientes.columns = ['Client', 'Cantidad']
                
                # Top 10
                top_clientes = top_clientes.sort_values(by='Cantidad', ascending=False).head(10)

                fig_re = px.bar(
                    top_clientes, 
                    x='Client', 
                    y='Cantidad', 
                    text='Cantidad', 
                    title=f"Top 10 Reincidentes ({opcion_reincidencia})",
                    color_discrete_sequence=['#FFD700']
                )
                
                # --- LÓGICA EJE Y (0 a 10) ---
                # Si el máximo es menor a 10, forzamos que llegue a 10.
                # Si es mayor (ej. 15), dejamos que Plotly se ajuste a 15 para no cortar la barra.
                max_val = top_clientes['Cantidad'].max()
                limite_superior = 10 if max_val <= 10 else (max_val + 1)

                fig_re.update_layout(
                    paper_bgcolor='white',   # Fondo Card
                    plot_bgcolor='white',    # Fondo Gráfica
                    font={'color': 'black'}, # Texto negro
                    margin=dict(t=50, l=50, r=50, b=50),
                    xaxis_title="Código Cliente", 
                    yaxis_title="Días con Incidencia",
                    xaxis=dict(type='category'),
                    # AQUI SE FUERZA EL RANGO DEL EJE Y
                    yaxis=dict(range=[0, limite_superior], dtick=1) # dtick=1 para que vaya de 1 en 1
                )
                
                fig_re.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig_re, use_container_width=True)
            else:
                st.info("No se encontraron reincidencias en el periodo seleccionado.")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
