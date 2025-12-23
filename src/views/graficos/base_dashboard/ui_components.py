# ui_components.py
import streamlit as st
import pandas as pd
import numpy as np
from config import ORDEN_FRANJAS, COLUMNAS_DEFECTO_CARTERA

def sidebar_filters(df):
    """Crea y devuelve los filtros de la barra lateral."""
    st.sidebar.header("Filtros de Cartera")
    
    filters = {}
    
    filters['empresa'] = st.sidebar.multiselect(
        "Empresa:",
        options=sorted(df["Empresa"].unique()),
        default=sorted(df["Empresa"].unique())
    )
    
    if 'CALL_CENTER_FILTRO' in df.columns:
        opciones_call_center = sorted(df['CALL_CENTER_FILTRO'].unique())
        filters['call_center'] = st.sidebar.multiselect(
            "Call Center:",
            options=opciones_call_center,
            default=opciones_call_center # Por defecto, seleccionamos todo.
        )

    if 'Zona' in df.columns:
        # Reemplazar posibles valores nulos en 'Zona' para evitar errores
        df['Zona'] = df['Zona'].fillna('SIN ZONA')
        
        opciones_zona = sorted(df["Zona"].unique())
        
        filters['Zona'] = st.sidebar.multiselect(
            "Zona:",
            options=opciones_zona,
            default=opciones_zona
        )
    # Filtro para Regional de Cobro
    if 'Regional_Cobro' in df.columns:
        # ----- INICIO DE LA MODIFICACIÓN -----
        # Reemplaza los valores nulos (NaN) por 'OTRAS ZONAS'
        # Usamos .astype(str) para asegurarnos de que 'nan' como texto también se reemplace
        df['Regional_Cobro'] = df['Regional_Cobro'].replace(np.nan, 'OTRAS ZONAS')
        df['Regional_Cobro'] = df['Regional_Cobro'].replace('nan', 'OTRAS ZONAS')
        
        # Obtenemos las opciones únicas después de haber hecho el reemplazo
        opciones_regional_cobro = sorted(df["Regional_Cobro"].unique())
        # ----- FIN DE LA MODIFICACIÓN -----

        filters['regional_cobro'] = st.sidebar.multiselect(
            "Regional de Cobro:",
            options=opciones_regional_cobro,
            default=opciones_regional_cobro
        )

    # Filtro para Franja de Cartera
    if 'Franja_Cartera' in df.columns:
        filters['franja_cartera'] = st.sidebar.multiselect(
            "Franja de Cartera:",
            options=sorted(df["Franja_Cartera"].unique()),
            default=sorted(df["Franja_Cartera"].unique())
        )
    
    filters['novedades'] = st.sidebar.radio(
        "Novedades:",
        ("Todos", "Con Novedades", "Sin Novedades")
    )
    
    return filters

def display_detailed_data(df, title, default_cols):
    """
    Muestra una tabla de datos con un selector de columnas OCULTO en un expander
    para ahorrar espacio y mantener la vista limpia.
    """
    # 1. Encabezado con conteo de registros (Mejor UX)
    col_header, col_count = st.columns([3, 1])
    with col_header:
        st.subheader(title)
    with col_count:
        st.markdown(f"<div style='text-align: right; padding-top: 10px; color: gray;'>Total: <b>{len(df):,}</b></div>", unsafe_allow_html=True)
    
    all_columns = df.columns.tolist()
    
    # 2. Envolvemos el selector en st.expander con expanded=False (Cerrado por defecto)
    with st.expander(f"Personalizar columnas de: {title}", expanded=False):
        
        # Generamos una 'key' única basada en el título para evitar errores de Streamlit
        # (Duplicate Widget ID) ya que usas esta función dos veces.
        unique_key = f"multiselect_{title.replace(' ', '_').lower()}"
        
        selected_columns = st.multiselect(
            "Selecciona las columnas visibles:",
            options=all_columns,
            default=[col for col in default_cols if col in all_columns],
            key=unique_key,
            label_visibility="collapsed" # Ocultamos la etiqueta interna para ganar más espacio
        )
    
    # 3. Mostramos la tabla usando st.data_editor (Más moderno y permite ordenar)
    if selected_columns:
        st.data_editor(
            df[selected_columns],
            use_container_width=True,
            hide_index=True,
            disabled=True, # Modo lectura, pero permite interactuar (ordenar, copiar)
            key=f"editor_{unique_key}" # Key única para la tabla también
        )
    else:
        st.warning("⚠️ Por favor selecciona al menos una columna para visualizar la tabla.")