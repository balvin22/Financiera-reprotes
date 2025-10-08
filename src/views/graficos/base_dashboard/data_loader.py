# data_loader.py
import streamlit as st
import pandas as pd

@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_data(uploaded_file):
    """
    Carga y procesa eficientemente los datos desde un archivo Excel,
    leyendo únicamente las columnas especificadas para optimizar el rendimiento.
    """
    # --- OPTIMIZACIÓN: Listas de columnas a cargar para cada hoja ---
    cols_cartera = [
        "Fecha_Desembolso", "Fecha_Ultima_Novedad", "Empresa", "Regional_Venta",
        "Nombre_Ciudad", "Nombre_Vendedor", "Franja_Meta", "Rodamiento", "Gestor",
        "Regional_Cobro", "Zona_Cobro", "Zona",
        "Cantidad_Novedades", "Cedula_Cliente", "Credito", "Nombre_Producto",
        "Obsequio", "Nombre_Cliente", "Correo", "Celular", "Direccion", "Barrio",
        "Nombre_Codeudor2", "Cobrador", "Telefono_Cobrador", "Call_Center_Apoyo",
        "Codigo_Vendedor", "Nombre_Call_Center", "Telefono_Call_Center",
        "Telefono_Gestor", "Valor_Desembolso", "Movil_Vendedor", "Vendedor_Activo",
        "Lider_Zona", "Codeudor1", "Total_Cuotas", "Nombre_Codeudor1",
        "Telefono_Codeudor1", "Ciudad_Codeudor1", "Codeudor2", "Telefono_Codeudor2",
        "Ciudad_Codeudor2", "Valor_Cuota", "Dias_Atraso", "Franja_Cartera",
        "Meta_Intereses", "Meta_Saldo", "Meta_%", "Meta_$", "Meta_T.R_%",
        "Meta_T.R_$", "Cuotas_Pagadas", "Fecha_Cuota_Atraso", "Primera_Cuota_Mora",
        "Valor_Cuota_Atraso", "Valor_Vencido", "Dias_Atraso_Final","Fecha_Ultimo_pago","Rango_Ultimo_pago",
        "Franja_Meta_Final", "Franja_Cartera_Final", "Rodamiento_Cartera","Valor_Cuota_Vigente",
        "Recaudo_Anticipado", "Recaudo_Meta", "Total_Recaudo", "Fecha_Cuota_Vigente","Total_Recaudo_Sin_Anti"
    ]
    
    cols_novedades = [
        "Fecha_Novedad", "Cedula_Cliente", "Nombre_Cliente", "Usuario_Novedad",
        "Nombre_Usuario", "Cargo_Usuario", "Celular_Corporativo", "Tipo_Novedad",
        "Novedad", "Fecha_Compromiso", "Valor","Empresa"
    ]

    try:
        # --- LECTURA CORREGIDA: Leemos cada hoja por separado para mayor fiabilidad ---
        
        # Cargar la hoja de Cartera
        df_cartera = pd.read_excel(
            uploaded_file, 
            sheet_name="Analisis_de_Cartera",
            engine='openpyxl',
            usecols=cols_cartera
        )
        
        # Cargar la hoja de Novedades
        df_novedades = pd.read_excel(
            uploaded_file,
            sheet_name="Detalle_Novedades",
            engine='openpyxl',
            usecols=cols_novedades
        )

        # --- Tu limpieza de datos se mantiene igual ---
        date_cols = ["Fecha_Desembolso", "Fecha_Ultima_Novedad", "Fecha_Cuota_Atraso", 
                     "Primera_Cuota_Mora",]
        for col in date_cols:
            if col in df_cartera.columns:
                df_cartera[col] = pd.to_datetime(df_cartera[col], errors="coerce").dt.date

        date_cols_novedades = ["Fecha_Novedad", "Fecha_Compromiso"]
        for col in date_cols_novedades:
             if col in df_novedades.columns:
                df_novedades[col] = pd.to_datetime(df_novedades[col], errors="coerce").dt.date

        str_cols = ["Empresa", "Regional_Venta", "Nombre_Ciudad", "Nombre_Vendedor", 
                    "Franja_Meta", "Rodamiento", "Gestor", "Regional_Cobro", 
                    "Zona_Cobro", "Zona"]
        for col in str_cols:
            if col in df_cartera.columns:
                df_cartera[col] = df_cartera[col].astype(str)

        if "Cantidad_Novedades" in df_cartera.columns:
            df_cartera['Cantidad_Novedades'] = pd.to_numeric(df_cartera['Cantidad_Novedades'], errors='coerce').fillna(0)

        if 'Cedula_Cliente' in df_cartera.columns:
            df_cartera['Cedula_Cliente'] = df_cartera['Cedula_Cliente'].astype(str).str.strip()

        if 'Cedula_Cliente' in df_novedades.columns:
            df_novedades['Cedula_Cliente'] = df_novedades['Cedula_Cliente'].astype(str).str.strip()
            
        return df_cartera, df_novedades

    except Exception as e:
        st.error(f"Error al leer el archivo. Asegúrate de que las hojas y columnas necesarias existan. Error: {e}")
        return None, None