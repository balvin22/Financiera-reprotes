import numpy as np
import pandas as pd 
import streamlit as st

def apply_main_filters(df_cartera, df_novedades, df_llamadas, df_mensajeria, filters):
    """
    Aplica los filtros de la barra lateral a todos los dataframes relevantes.
    [MODIFICADO]
    - Cartera/Novedades se filtran por TODOS los filtros.
    - Llamadas/Mensajería se filtran SÓLO por el filtro de 'call_center'.
    """
    
    # --- SECCIÓN 1: Filtrar Cartera y Novedades (Usando TODOS los filtros) ---
    
    df_cartera_filtrada = df_cartera[
        df_cartera["Empresa"].isin(filters['empresa']) &
        df_cartera["Regional_Cobro"].isin(filters['regional_cobro']) &
        df_cartera["Franja_Cartera"].isin(filters['franja_cartera']) &
        df_cartera["Zona"].isin(filters['Zona']) &
        df_cartera["CALL_CENTER_FILTRO"].isin(filters.get('call_center', df_cartera["CALL_CENTER_FILTRO"].unique()))
    ].copy()

    # (Filtrado de novedades no cambia)
    if filters['novedades'] == "Con Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] > 0]
    elif filters['novedades'] == "Sin Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] == 0]

    cedulas_filtradas = df_cartera_filtrada["Cedula_Cliente"].unique()
    if not df_novedades.empty:
        df_novedades_filtrada = df_novedades[df_novedades["Cedula_Cliente"].isin(cedulas_filtradas)]
    else:
        df_novedades_filtrada = pd.DataFrame(columns=df_novedades.columns)

    
    # --- SECCIÓN 2: Filtrar Llamadas y Mensajería (Usando SÓLO el filtro de Call Center) ---

    codigos_call_seleccionados = filters.get('call_center', [])
    df_llamadas_filtrada = pd.DataFrame(columns=df_llamadas.columns)
    df_mensajeria_filtrada = pd.DataFrame(columns=df_mensajeria.columns)

    # Filtrar Llamadas
    if not df_llamadas.empty and 'Call_Center' in df_llamadas.columns:
        df_llamadas_limpio = df_llamadas.copy()
        df_llamadas_limpio['Call_Center_Limpio'] = df_llamadas_limpio['Call_Center'].astype(str).str.replace(" ", "").str.strip().str.upper()
        df_llamadas_filtrada = df_llamadas_limpio[
            df_llamadas_limpio['Call_Center_Limpio'].isin(codigos_call_seleccionados)
        ]
        
    # Filtrar Mensajería
    if not df_mensajeria.empty and 'Call_Center' in df_mensajeria.columns:
        df_mensajeria_limpio = df_mensajeria.copy()
        df_mensajeria_limpio['Call_Center_Limpio'] = df_mensajeria_limpio['Call_Center'].astype(str).str.replace(" ", "").str.strip().str.upper()
        
        df_mensajeria_filtrada = df_mensajeria_limpio[
            df_mensajeria_limpio['Call_Center_Limpio'].isin(codigos_call_seleccionados)
        ]
    
    return df_cartera_filtrada, df_novedades_filtrada, df_llamadas_filtrada, df_mensajeria_filtrada


def add_call_center_column(df):
    """
    Crea una nueva columna 'CALL_CENTER_FILTRO' unificando los valores
    de 'Zona' (para CL1-CL4) y 'Call_Center_Apoyo' (para CL5-CL9).
    """
    df_copy = df.copy()

    if 'Zona' not in df_copy.columns:
        df_copy['Zona'] = ''
    else:
        df_copy['Zona'] = df_copy['Zona'].astype(str).str.replace(" ", "").str.strip().str.upper().fillna('')

    if 'Call_Center_Apoyo' not in df_copy.columns:
        df_copy['Call_Center_Apoyo'] = ''
    else:
        df_copy['Call_Center_Apoyo'] = df_copy['Call_Center_Apoyo'].astype(str).str.replace(" ", "").str.strip().str.upper().fillna('')

    conditions = [
        df_copy['Zona'].isin(['CL1', 'CL2', 'CL3', 'CL4']),
        df_copy['Call_Center_Apoyo'].isin(['CL5', 'CL6', 'CL7', 'CL8', 'CL9'])
    ]
    choices = [
        df_copy['Zona'],
        df_copy['Call_Center_Apoyo']
    ]
    
    df_copy['CALL_CENTER_FILTRO'] = np.select(conditions, choices, default='SIN CALL CENTER')
    
    return df_copy

