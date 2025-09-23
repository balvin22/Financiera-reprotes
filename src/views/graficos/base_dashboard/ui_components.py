# ui_components.py
import streamlit as st
import pandas as pd
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

    opciones_franja = [f for f in ORDEN_FRANJAS if f in df["Franja_Meta"].unique()]
    filters['franjas'] = st.sidebar.multiselect(
        "Franja de Meta:",
        options=opciones_franja,
        default=opciones_franja
    )
    # Filtro para Regional de Cobro
    if 'Regional_Cobro' in df.columns:
        filters['regional_cobro'] = st.sidebar.multiselect(
            "Regional de Cobro:",
            options=sorted(df["Regional_Cobro"].unique()),
            default=sorted(df["Regional_Cobro"].unique())
        )

    # Filtro para Franja de Cartera
    if 'Franja_Cartera' in df.columns:
        filters['franja_cartera'] = st.sidebar.multiselect(
            "Franja de Cartera:",
            options=sorted(df["Franja_Cartera"].unique()),
            default=sorted(df["Franja_Cartera"].unique())
        )
    

    # ... Añade aquí los demás multiselect para Regional, Gestor, Rodamiento ...

    filters['novedades'] = st.sidebar.radio(
        "Novedades:",
        ("Todos", "Con Novedades", "Sin Novedades")
    )
    
    return filters

def display_detailed_data(df, title, default_cols):
    """Muestra un selector de columnas y una tabla de datos."""
    st.subheader(title)
    all_columns = df.columns.tolist()
    
    selected_columns = st.multiselect(
        f"Selecciona columnas para la tabla '{title}':",
        options=all_columns,
        default=[col for col in default_cols if col in all_columns]
    )
    
    if selected_columns:
        st.dataframe(df[selected_columns])