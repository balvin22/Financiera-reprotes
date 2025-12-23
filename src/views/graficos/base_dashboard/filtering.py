# filtering.py
import numpy as np
import pandas as pd 
import streamlit as st

def apply_main_filters(df_cartera, df_novedades, df_llamadas, df_mensajeria, filters):
    """
    Aplica los filtros de la barra lateral.
    RETORNA DOS VERSIONES DE CARTERA:
    1. df_cartera_clasica: Lógica Antigua (Estricta por 'CALL_CENTER_FILTRO') -> Tabs 1-5.
    2. df_cartera_tab6: Lógica Nueva (Inclusiva Zona O Apoyo) -> Tab 6.
    """
    
    # --- A. FILTROS COMUNES (Empresa, Regional, Franja, Zona Geográfica) ---
    mask_common = (
        df_cartera["Empresa"].isin(filters['empresa']) &
        df_cartera["Regional_Cobro"].isin(filters['regional_cobro']) &
        df_cartera["Franja_Cartera"].isin(filters['franja_cartera']) &
        df_cartera["Zona"].isin(filters['Zona'])
    )
    
    # Base con filtros comunes ya aplicados
    df_base = df_cartera[mask_common].copy()
    
    seleccion_cc = filters.get('call_center', [])

    # =========================================================================
    # CAMINO 1: CARTERA CLÁSICA (Para Tabs 1, 2, 3, 4, 5)
    # Lógica: Usamos la columna 'CALL_CENTER_FILTRO' que viene de tu lógica original.
    # Esto asegura que los gráficos antiguos NO CAMBIEN.
    # =========================================================================
    if seleccion_cc:
        # Filtro estricto: Solo si coincide con la etiqueta asignada originalmente
        mask_strict = df_base["CALL_CENTER_FILTRO"].isin(seleccion_cc)
        df_cartera_clasica = df_base[mask_strict].copy()
    else:
        df_cartera_clasica = df_base.copy()

    # =========================================================================
    # CAMINO 2: CARTERA TAB 6 (Para el Módulo Call Center)
    # Lógica: Inclusiva. Buscamos en 'Zona' O en 'Call_Center_Apoyo'.
    # Esto asegura que el Tab 6 reciba las 148 cuentas (114 + 34).
    # =========================================================================
    if seleccion_cc:
        col_zona = df_base["Zona"].astype(str).str.strip().str.upper()
        col_apoyo = df_base.get("Call_Center_Apoyo", pd.Series()).astype(str).str.strip().str.upper()
        
        # Condición OR: ¿Está en Zona O está en Apoyo?
        mask_inclusive = (col_zona.isin(seleccion_cc) | col_apoyo.isin(seleccion_cc))
        df_cartera_tab6 = df_base[mask_inclusive].copy()
    else:
        df_cartera_tab6 = df_base.copy()

    # =========================================================================
    # FILTRO DE NOVEDADES
    # =========================================================================
    if filters['novedades'] == "Con Novedades":
        df_cartera_clasica = df_cartera_clasica[df_cartera_clasica["Cantidad_Novedades"] > 0]
        df_cartera_tab6 = df_cartera_tab6[df_cartera_tab6["Cantidad_Novedades"] > 0]
    elif filters['novedades'] == "Sin Novedades":
        df_cartera_clasica = df_cartera_clasica[df_cartera_clasica["Cantidad_Novedades"] == 0]
        df_cartera_tab6 = df_cartera_tab6[df_cartera_tab6["Cantidad_Novedades"] == 0]

    # Para el DF de novedades, usamos las cédulas del Tab 6 (que es el más completo) para no perder datos
    cedulas_filtradas = df_cartera_tab6["Cedula_Cliente"].unique()
    
    if not df_novedades.empty:
        df_novedades_filtrada = df_novedades[df_novedades["Cedula_Cliente"].isin(cedulas_filtradas)]
    else:
        df_novedades_filtrada = pd.DataFrame(columns=df_novedades.columns)

    # =========================================================================
    # FILTRO LLAMADAS Y MENSAJERÍA
    # =========================================================================
    df_llamadas_filtrada = pd.DataFrame(columns=df_llamadas.columns)
    df_mensajeria_filtrada = pd.DataFrame(columns=df_mensajeria.columns)

    if not df_llamadas.empty and 'Call_Center' in df_llamadas.columns:
        df_l = df_llamadas.copy()
        df_l['Call_Center_Limpio'] = df_l['Call_Center'].astype(str).str.replace(" ", "").str.strip().str.upper()
        df_llamadas_filtrada = df_l[df_l['Call_Center_Limpio'].isin(seleccion_cc)] if seleccion_cc else df_l
        
    if not df_mensajeria.empty and 'Call_Center' in df_mensajeria.columns:
        df_m = df_mensajeria.copy()
        df_m['Call_Center_Limpio'] = df_m['Call_Center'].astype(str).str.replace(" ", "").str.strip().str.upper()
        df_mensajeria_filtrada = df_m[df_m['Call_Center_Limpio'].isin(seleccion_cc)] if seleccion_cc else df_m
    
    # IMPORTANTE: Retornamos 5 valores, separando la cartera en dos
    return df_cartera_clasica, df_cartera_tab6, df_novedades_filtrada, df_llamadas_filtrada, df_mensajeria_filtrada


def add_call_center_column(df):
    """
    Mantenemos tu lógica ORIGINAL e INTACTA para que los Tabs 1-5 no cambien.
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

    # --- TU LÓGICA ANTIGUA ---
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