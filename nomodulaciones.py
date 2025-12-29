import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analizador de Hoja Específica", layout="wide")

st.title("📂 Extractor de Hoja 3.30.8")
st.write("Sube un archivo Excel para extraer específicamente la hoja **3.30.8**.")

uploaded_file = st.file_uploader("Elige un archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        # Usamos pd.ExcelFile para inspeccionar los nombres de las hojas sin cargar todo el contenido aún
        excel_file = pd.ExcelFile(uploaded_file)
        nombres_hojas = excel_file.sheet_names
        
        hoja_objetivo = "3.30.8"

        if hoja_objetivo in nombres_hojas:
            st.success(f"✅ Hoja '{hoja_objetivo}' encontrada.")
            
            # Leer solo la hoja específica
            df_hoja = pd.read_excel(uploaded_file, sheet_name=hoja_objetivo)

            if df_hoja.empty:
                st.warning(f"La hoja '{hoja_objetivo}' está vacía.")
            else:
                st.subheader(f"📊 Datos de la hoja: {hoja_objetivo}")
                st.dataframe(df_hoja) # Muestra toda la hoja o puedes usar .head()
        else:
            st.error(f"❌ La hoja '{hoja_objetivo}' no se encuentra en este archivo.")
            st.info(f"Hojas disponibles: {', '.join(nombres_hojas)}")

    except Exception as e:
        st.error(f"Hubo un error al procesar el archivo: {e}")
