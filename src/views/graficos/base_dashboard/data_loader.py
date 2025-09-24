# data_loader.py
import streamlit as st
import pandas as pd



@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_data(uploaded_file):
    """
    Carga y procesa los datos desde el archivo Excel subido.
    Devuelve dos DataFrames: cartera y novedades.
    """
    try:
        df_cartera = pd.read_excel(uploaded_file, sheet_name="Analisis_de_Cartera")
        df_novedades = pd.read_excel(uploaded_file, sheet_name="Detalle_Novedades")

        # --- Limpieza y conversión de tipos ---
        date_cols = ["Fecha_Desembolso", "Fecha_Ultima_Novedad"]
        for col in date_cols:
            if col in df_cartera.columns:
                df_cartera[col] = pd.to_datetime(df_cartera[col], errors="coerce").dt.date

        if "Fecha_Novedad" in df_novedades.columns:
            df_novedades["Fecha_Novedad"] = pd.to_datetime(df_novedades["Fecha_Novedad"], errors="coerce").dt.date

        str_cols = ["Empresa", "Regional_Venta", "Nombre_Ciudad", "Nombre_Vendedor", "Franja_Meta", "Rodamiento", "Gestor", "Regional_Cobro", "Zona_Cobro","Zona", "Celular_Corporativo"]
        for col in str_cols:
            if col in df_cartera.columns:
                df_cartera[col] = df_cartera[col].astype(str)

        if "Cantidad_Novedades" in df_cartera.columns:
            df_cartera['Cantidad_Novedades'] = pd.to_numeric(df_cartera['Cantidad_Novedades'], errors='coerce').fillna(0)

        # Esto asegura que ambas columnas se traten como texto limpio y sin espacios.
        if 'Cedula_Cliente' in df_cartera.columns:
            # Convierte a texto y quita espacios en blanco de los lados
            df_cartera['Cedula_Cliente'] = df_cartera['Cedula_Cliente'].astype(str).str.strip()

        if 'Cedula_Cliente' in df_novedades.columns:
            # Convierte a texto y quita espacios en blanco de los lados
            df_novedades['Cedula_Cliente'] = df_novedades['Cedula_Cliente'].astype(str).str.strip()
        # --- FIN DE LA SECCIÓN AÑADIDA ---    

        return df_cartera, df_novedades
    except Exception as e:
        st.error(f"Error al leer el archivo. Asegúrate de que las hojas 'Analisis_de_Cartera' y 'Detalle_Novedades' existan. Error: {e}")
        return None, None