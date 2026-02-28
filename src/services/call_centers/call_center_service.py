import pandas as pd
import numpy as np
import streamlit as st

from .sub_llamadas_service import process_llamadas
from .sub_mensajeria_service import process_mensajeria_funnel
from .sub_novedades_service import process_novedades_system

ALL_CALL_CENTERS = [f'CL{i}' for i in range(1, 10)]

def _handle_empty_input():
    return {
        "reporte_raw": pd.DataFrame(), "rodamiento_data": pd.DataFrame(),
        "cartera_detallada_call_center": pd.DataFrame(), "df_llamadas_filtrada": pd.DataFrame(),
        "df_mensajeria_filtrada": pd.DataFrame(),
        "llamadas_stats": {"total_llamadas": 0, "con_respuesta": 0, "sin_respuesta": 0},
        "df_grafico_llamadas": pd.DataFrame(), "df_efectividad_call": pd.DataFrame(),
        "df_llamadas_por_dia": pd.DataFrame(), "alerta_umbral": 0,
        "df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame(),
        "df_novedades_mapeadas": pd.DataFrame(), "df_agg_novedades_por_call": pd.DataFrame(),
        "df_agg_novedades_por_tipo": pd.DataFrame()
    }

def _clean_cartera_df(df: pd.DataFrame) -> pd.DataFrame:
    # Ya no convertimos a numérico ni a string, el Parquet ya lo hizo
    if 'Total_Recaudo' in df.columns:
        df['Estado_Pago'] = np.where(df['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
    if 'Cantidad_Novedades' in df.columns:
        df['Estado_Gestion'] = np.where(df['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')
    return df

def _merge_cartera_with_novedades(df_detalle: pd.DataFrame, df_novedades: pd.DataFrame) -> pd.DataFrame:
    if df_novedades.empty or 'Cedula_Cliente' not in df_novedades.columns:
        df_detalle['Tipo_Novedad'] = 'SIN NOVEDAD'
        df_detalle['Novedad'] = ''
        return df_detalle

    cols_to_merge = ['Cedula_Cliente', 'Tipo_Novedad', 'Novedad']
    
    # --- Mantenemos solo la última novedad por cédula ---
    df_novedades_detalle = df_novedades[cols_to_merge].drop_duplicates(subset=['Cedula_Cliente'], keep='last').copy()
    
    df_detalle = df_detalle.merge(df_novedades_detalle, on='Cedula_Cliente', how='left')
    df_detalle['Tipo_Novedad'] = df_detalle['Tipo_Novedad'].fillna('SIN NOVEDAD')
    df_detalle['Novedad'] = df_detalle['Novedad'].fillna('')
    return df_detalle

def _process_cartera_and_report(df_cartera: pd.DataFrame, df_novedades: pd.DataFrame) -> dict:
    df = _clean_cartera_df(df_cartera)
    
    mask_zona_al_dia = (df['Zona'].isin(ALL_CALL_CENTERS)) & (df['Franja_Meta'] == 'AL DIA')
    # Evitamos copies innecesarios
    df_zona = df[mask_zona_al_dia]
    
    mask_apoyo_general = df['Call_Center_Apoyo'].isin(ALL_CALL_CENTERS)
    mask_apoyo_final = mask_apoyo_general & (~mask_zona_al_dia)
    df_apoyo = df[mask_apoyo_final]

    df_zona_norm = df_zona[['Zona', 'Cobrador', 'Meta_General', 'Recaudo_Meta', 'Rodamiento', 'Cedula_Cliente', 'Credito']].rename(
        columns={'Zona': 'CALL_CENTER_ID', 'Cobrador': 'NOMBRE_AGENTE', 'Meta_General': 'META_UNIFICADA'}
    )
    
    df_apoyo_norm = df_apoyo[['Call_Center_Apoyo', 'Nombre_Call_Center', 'Meta_$', 'Recaudo_Meta', 'Rodamiento', 'Cedula_Cliente', 'Credito']].rename(
        columns={'Call_Center_Apoyo': 'CALL_CENTER_ID', 'Nombre_Call_Center': 'NOMBRE_AGENTE', 'Meta_$': 'META_UNIFICADA'}
    )

    df_total_unificado = pd.concat([df_zona_norm, df_apoyo_norm], ignore_index=True)
    
    agg_total = pd.DataFrame()
    if not df_total_unificado.empty:
        agg_total = df_total_unificado.groupby(['CALL_CENTER_ID', 'NOMBRE_AGENTE'], observed=True).agg(
            **{'META_$': ('META_UNIFICADA', 'sum'), 'Recaudo_Meta': ('Recaudo_Meta', 'sum')}
        ).reset_index().rename(columns={'CALL_CENTER_ID': 'CALL_CENTER', 'NOMBRE_AGENTE': 'NOMBRE'})
        agg_total['Franja'] = 'CONSOLIDADO' 

    reporte_raw = pd.DataFrame()
    if not agg_total.empty:
        agg_total['Faltante'] = agg_total['META_$'] - agg_total['Recaudo_Meta']
        agg_total['Cumplimiento'] = np.where(agg_total['META_$'] > 0, agg_total['Recaudo_Meta'] / agg_total['META_$'], 0)
        reporte_raw = agg_total[['CALL_CENTER', 'NOMBRE', 'Franja', 'META_$', 'Recaudo_Meta', 'Faltante', 'Cumplimiento']].sort_values(by='CALL_CENTER').reset_index(drop=True)

    agg_rodamiento = pd.DataFrame()
    if not df_total_unificado.empty and 'Rodamiento' in df_total_unificado.columns:
        agg_rodamiento = df_total_unificado.groupby('Rodamiento', dropna=False, observed=True).size().reset_index(name='count')

    # Concatenamos y aplicamos un blindaje extra por crédito
    df_base_unica_raw = pd.concat([df_zona, df_apoyo], ignore_index=True).drop_duplicates(subset=['Credito'])
    df_detalle_final = _merge_cartera_with_novedades(df_base_unica_raw, df_novedades)

    return {
        "reporte_raw": reporte_raw, "rodamiento_data": agg_rodamiento,
        "cartera_detallada_call_center": df_detalle_final, 
        "novedades_crudas": df_novedades, # Enviamos todas las novedades crudas al frontend
        "df_cartera_procesada": df 
    }

# --- NUEVA FUNCIÓN DE LIMPIEZA MAESTRA ---
def _limpiar_nans_y_vacios(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """Filtra y elimina de raíz los registros donde el Call Center sea NAN, vacío o inválido."""
    if df.empty or col_name not in df.columns:
        return df
    
    # 1. Convertir a texto, quitar espacios invisibles y poner en mayúsculas
    col_sucia = df[col_name].astype(str).str.strip().str.upper()
    
    # 2. Crear máscara estricta que rechace cualquier formato de "vacío"
    mask_validos = ~col_sucia.isin(['NAN', 'NONE', 'NULL', '', '<NA>'])
    
    # 3. Retornar el DataFrame completamente purgado
    return df[mask_validos].copy()


def prepare_tab6_data(df_cartera_filtrada: pd.DataFrame, df_novedades_filtrada: pd.DataFrame, df_llamadas_filtrada: pd.DataFrame, df_mensajeria_filtrada: pd.DataFrame) -> dict: 
    if df_cartera_filtrada.empty:
        st.warning("No hay datos de cartera para procesar en el Tab 6.")
        return _handle_empty_input()
    
    # =====================================================================
    # EL COLADOR: Limpiamos los datos antes de dárselos a los sub-servicios
    # =====================================================================
    if 'Call_Center_Limpio' in df_llamadas_filtrada.columns:
        df_llamadas_filtrada = _limpiar_nans_y_vacios(df_llamadas_filtrada, 'Call_Center_Limpio')
        
    if 'Call_Center_Limpio' in df_mensajeria_filtrada.columns:
        df_mensajeria_filtrada = _limpiar_nans_y_vacios(df_mensajeria_filtrada, 'Call_Center_Limpio')

    # Pasamos las vistas purificadas a los procesadores
    cartera_data = _process_cartera_and_report(df_cartera_filtrada, df_novedades_filtrada)
    llamadas_data = process_llamadas(df_llamadas_filtrada)
    
    df_cartera_procesada = cartera_data["df_cartera_procesada"]
    mensajeria_data = process_mensajeria_funnel(df_mensajeria_filtrada, df_novedades_filtrada, df_cartera_procesada)
    
    novedades_sistema_data = process_novedades_system(df_novedades_filtrada, df_llamadas_filtrada)

    final_data = {
        **cartera_data, **llamadas_data, **mensajeria_data, **novedades_sistema_data, 
        "df_llamadas_filtrada": df_llamadas_filtrada,
        "df_mensajeria_filtrada": df_mensajeria_filtrada, 
    }
    
    if "df_cartera_procesada" in final_data:
        del final_data["df_cartera_procesada"]
    
    return final_data