import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Reporte de modulación", layout="wide")

# --- INYECCIÓN DE CSS GLOBAL ---
st.markdown("""
    <style>
    .tabla-final {
        width: 100%;
        border-collapse: collapse;
        border: 2px solid white !important;
        font-family: Arial, sans-serif;
    }
    .tabla-final thead th {
        background-color: #FFD700 !important; /* Amarillo */
        color: black !important; /* Texto Negro */
        text-align: center !important;
        padding: 12px !important;
        border: 2px solid white !important;
    }
    .tabla-final tbody td {
        background-color: #F8F9FA !important;
        color: black !important;
        text-align: center !important;
        padding: 10px !important;
        border: 2px solid white !important;
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
        
        # Filtro DPS 88
        df_base = df[df['DPS'].astype(str).str.contains('88')].copy()

        # Función para detectar validez en BUSCA (Detecta #N/D, errores, vacíos)
        def es_valido(valor):
            if pd.isna(valor) or valor == "" or "error" in str(valor).lower() or "#" in str(valor):
                return False
            try:
                float(str(valor).replace(',', '.'))
                return True
            except ValueError:
                return False

        df_base['es_modulado'] = df_base['BUSCA'].apply(es_valido)

        # --- SECCIÓN 1: GRÁFICO EVOLUCIÓN ---
        st.markdown("### Evolución de Modulación")
        opcion_graf = st.selectbox("Selecciona el periodo:", ["Últimos 7 días", "Mes Actual", "Histórico"])
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

        fig = px.bar(resumen, x=resumen.columns[0], y='% Modulación', text='% Modulación', color_discrete_sequence=['#FFD700'])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 2: CLIENTES NO MODULADOS (TABLA) ---
        st.markdown("---")
        st.header("DIARIO")
        st.subheader("NO MODULACIÓN")
        
        df_no_mod = df_base[df_base['es_modulado'] == False].copy()

        if not df_no_mod.empty:
            fecha_sel = st.selectbox("Filtrar por fecha:", sorted(df_no_mod['Fecha'].unique(), reverse=True))
            df_f = df_no_mod[df_no_mod['Fecha'] == fecha_sel].copy()

            # Conversión forzada a string limpio para Client
            for col in ['Client', 'F.Pedido']:
                if col in df_f.columns:
                    df_f[col] = df_f[col].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))
            
            if 'Motivo' in df_f.columns:
                df_f['Motivo'] = df_f['Motivo'].astype(str).replace(['nan', 'None'], 'Sin Motivo')

            resultado = df_f.drop_duplicates(subset=['Client'], keep='first')
            cols = [c for c in ['Client', 'Cam', 'F.Pedido', 'Motivo'] if c in resultado.columns]

            html_tabla = resultado[cols].to_html(index=False, classes='tabla-final')
            
            st.write(f"Clientes encontrados: **{len(resultado)}**")
            st.markdown(html_tabla, unsafe_allow_html=True)
            
        else:
            st.warning("No hay datos para Clientes No Modulados.")

        # --- SECCIÓN 3: REINCIDENCIAS (NUEVO) ---
        st.markdown("---")
        st.header("REINCIDENCIAS")
        st.subheader("Clientes más reincidentes (#N/D)")

        # Usamos df_no_mod que ya tiene: DPS=88 y BUSCA con error/#N/D
        if not df_no_mod.empty:
            col_filt_re, col_blank = st.columns([1, 3])
            with col_filt_re:
                opcion_reincidencia = st.selectbox("Periodo Reincidencia:", ["Últimos 7 días", "Mes Actual", "Último Año"])
            
            df_re = df_no_mod.copy()
            # Aseguramos limpieza del nombre del cliente para agrupar bien
            df_re['Client'] = df_re['Client'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit() else str(x))

            top_clientes = pd.DataFrame()
            y_axis_label = "Cantidad de Errores"

            if opcion_reincidencia == "Últimos 7 días":
                fecha_limite = ultima_fecha - pd.Timedelta(days=7)
                df_re_filt = df_re[df_re['Entrega'] > fecha_limite]
                # Conteo simple
                top_clientes = df_re_filt['Client'].value_counts().reset_index()
                top_clientes.columns = ['Client', 'Cantidad']
                y_axis_label = "Cantidad"

            elif opcion_reincidencia == "Mes Actual":
                df_re_filt = df_re[
                    (df_re['Entrega'].dt.month == ultima_fecha.month) & 
                    (df_re['Entrega'].dt.year == ultima_fecha.year)
                ]
                # Conteo simple
                top_clientes = df_re_filt['Client'].value_counts().reset_index()
                top_clientes.columns = ['Client', 'Cantidad']
                y_axis_label = "Cantidad"

            else: # Último Año (Promedio por mes)
                fecha_limite = ultima_fecha - pd.DateOffset(years=1)
                df_re_filt = df_re[df_re['Entrega'] > fecha_limite].copy()
                
                # Creamos columna mes-año para agrupar
                df_re_filt['Mes_Anio'] = df_re_filt['Entrega'].dt.to_period('M')
                
                # 1. Contamos errores por cliente y por mes
                conteo_mensual = df_re_filt.groupby(['Client', 'Mes_Anio']).size().reset_index(name='Conteo')
                
                # 2. Sacamos el promedio de esos conteos mensuales
                top_clientes = conteo_mensual.groupby('Client')['Conteo'].mean().reset_index()
                top_clientes.columns = ['Client', 'Promedio']
                y_axis_label = "Promedio Mensual"

            # Ordenar y tomar Top 15 para que la gráfica no se sature
            if not top_clientes.empty:
                col_val = top_clientes.columns[1] # 'Cantidad' o 'Promedio'
                top_clientes = top_clientes.sort_values(by=col_val, ascending=False).head(15)

                fig_re = px.bar(
                    top_clientes, 
                    x='Client', 
                    y=col_val, 
                    text=col_val, 
                    title=f"Top 15 Clientes Reincidentes - {opcion_reincidencia}",
                    color_discrete_sequence=['#FFD700'] # Amarillo
                )
                
                fig_re.update_layout(xaxis_title="Cliente", yaxis_title=y_axis_label)
                # Formato del texto (si es promedio usa decimales, si es cantidad enteros)
                formato = '.1f' if opcion_reincidencia == "Último Año" else 'd'
                fig_re.update_traces(texttemplate=f'%{{text:{formato}}}', textposition='outside')
                
                st.plotly_chart(fig_re, use_container_width=True)
            else:
                st.info("No hay reincidencias en el periodo seleccionado.")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
