import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Modulación 3.30.8", layout="wide")

st.title("📊 Análisis de Modulación por Periodos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Cargar datos
        df = pd.read_excel(uploaded_file, sheet_name="3.30.8")

        # --- PROCESAMIENTO ---
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

        # --- FILTROS DE TIEMPO ---
        opcion = st.selectbox(
            "Selecciona el periodo de análisis:",
            ["Últimos 7 días", "Mes Actual (Calendario)", "Promedio Mensual (Histórico)"]
        )

        # Fecha de referencia (la más reciente en el archivo)
        ultima_fecha = df_base['Entrega'].max()
        
        if opcion == "Últimos 7 días":
            fecha_limite = (ultima_fecha - pd.Timedelta(days=7)).date()
            df_final = df_base[df_base['Fecha'] > fecha_limite]
            agrupar_por = 'Fecha'
            
        elif opcion == "Mes Actual (Calendario)":
            # Filtra solo los días que pertenecen al mismo Mes y Año de la última fecha
            mes_actual = ultima_fecha.month
            anio_actual = ultima_fecha.year
            df_final = df_base[(df_base['Entrega'].dt.month == mes_actual) & 
                               (df_base['Entrega'].dt.year == anio_actual)]
            agrupar_por = 'Fecha'
            
        else: # Promedio Mensual
            df_final = df_base.copy()
            df_final['Periodo'] = df_base['Entrega'].dt.to_period('M')
            agrupar_por = 'Periodo'

        # --- GENERACIÓN DE TABLA ---
        resumen = df_final.groupby(agrupar_por).apply(
            lambda x: pd.Series({
                'Total Concatenados': x['CONCATENADO'].nunique(),
                'Modulados': x[x['es_modulado']]['CONCATENADO'].nunique()
            })
        ).reset_index()

        resumen['% Modulación'] = (resumen['Modulados'] / resumen['Total Concatenados']) * 100
        resumen = resumen.sort_values(by=agrupar_por, ascending=False)

        # --- VISUALIZACIÓN ---
        st.markdown("---")
        nombre_mes = ultima_fecha.strftime('%B %Y') if opcion == "Mes Actual (Calendario)" else opcion
        st.subheader(f"Vista: {nombre_mes}")
        
        formatos = {
            'Total Concatenados': '{:,.0f}',
            'Modulados': '{:,.0f}',
            '% Modulación': '{:.2f}%'
        }
        
        if agrupar_por == 'Fecha':
            formatos['Fecha'] = lambda x: x.strftime('%d/%m/%Y')
        else:
            formatos['Periodo'] = lambda x: str(x)

        st.dataframe(
            resumen.style.format(formatos), 
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:
        st.error(f"Error al procesar el archivo. Asegúrate de que las columnas sean correctas.")
