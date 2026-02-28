# filtering.py
import numpy as np
import pandas as pd 
import streamlit as st

def apply_main_filters(df_cartera, df_novedades, df_llamadas, df_mensajeria, filters):
    """
    Aplica los filtros de la barra lateral.
    Con lógica inteligente: Si el filtro está vacío, no se aplica (Muestra todo).
    """
    
    # --- A. FILTROS COMUNES DINÁMICOS ---
    mask_common = pd.Series(True, index=df_cartera.index)
    
    if filters.get('empresa'):
        mask_common &= df_cartera["Empresa"].isin(filters['empresa'])
        
    if filters.get('regional_cobro'):
        mask_common &= df_cartera["Regional_Cobro"].isin(filters['regional_cobro'])
        
    if filters.get('franja_cartera'):
        mask_common &= df_cartera["Franja_Cartera"].isin(filters['franja_cartera'])
        
    if filters.get('Zona'):
        mask_common &= df_cartera["Zona"].isin(filters['Zona'])
        
    # --- NUEVO FILTRO DE VIGENCIA APLICADO GLOBALMENTE ---
    if filters.get('vigencia'):
        mask_common &= df_cartera["Estado_Vigencia_Filtro"].isin(filters['vigencia'])
    
    df_base = df_cartera[mask_common].copy()
    
    seleccion_cc = filters.get('call_center', [])

    # =========================================================================
    # CAMINO 1: CARTERA CLÁSICA (Para Tabs 1-5)
    # =========================================================================
    if seleccion_cc:
        mask_strict = df_base["CALL_CENTER_FILTRO"].isin(seleccion_cc)
        df_cartera_clasica = df_base[mask_strict].copy()
    else:
        df_cartera_clasica = df_base.copy()

    # =========================================================================
    # CAMINO 2: CARTERA TAB 6 (Para el Módulo Call Center)
    # =========================================================================
    if seleccion_cc:
        col_zona = df_base["Zona"].astype(str).str.strip().str.upper()
        col_apoyo = df_base.get("Call_Center_Apoyo", pd.Series()).astype(str).str.strip().str.upper()
        
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
    
    return df_cartera_clasica, df_cartera_tab6, df_novedades_filtrada, df_llamadas_filtrada, df_mensajeria_filtrada


def add_call_center_column(df):
    """
    Agrega la lógica original de Call Center y crea la nueva columna de Vigencia Global.
    """
    df_copy = df.copy()

    # --- LÓGICA DE CALL CENTER ---
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
    
    # --- NUEVA LÓGICA: ESTADO DE VIGENCIA GLOBAL ---
    # Convertimos los datos crudos a las 3 opciones exactas
    if 'Fecha_Cuota_Vigente' in df_copy.columns:
        fechas = pd.to_datetime(df_copy['Fecha_Cuota_Vigente'], errors='coerce')
        texto_vigencia = df_copy['Fecha_Cuota_Vigente'].astype(str).str.upper().str.strip()
        
        condiciones_vigencia = [
            fechas.notna(),  # Si es una fecha válida, cuenta como "Vigentes"
            texto_vigencia.str.contains('ANTICIPADO', na=False) # Si dice anticipado
        ]
        # Si no es fecha ni anticipado (ej. VIGENCIA EXPIRADA), es "Vencidos"
        df_copy['Estado_Vigencia_Filtro'] = np.select(condiciones_vigencia, ['Vigentes', 'Anticipados'], default='Vencidos')
    else:
        df_copy['Estado_Vigencia_Filtro'] = 'Sin Dato'
    
    return df_copy