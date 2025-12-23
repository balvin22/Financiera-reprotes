# src/services/call_centers/call_center_service.py
import pandas as pd
import numpy as np
import streamlit as st
import unicodedata 

from .sub_llamadas_service import process_llamadas
from .sub_mensajeria_service import process_mensajeria_funnel
from .sub_novedades_service import process_novedades_system

# --- Constantes de Configuración ---
ALL_CALL_CENTERS = [f'CL{i}' for i in range(1, 10)]

# --- 1. Función Ayudante: Datos Vacíos ---
def _handle_empty_input():
    return {
        "reporte_raw": pd.DataFrame(),
        "rodamiento_data": pd.DataFrame(),
        "cartera_detallada_call_center": pd.DataFrame(),
        "df_llamadas_filtrada": pd.DataFrame(),
        "df_mensajeria_filtrada": pd.DataFrame(),
        "llamadas_stats": {"total_llamadas": 0, "con_respuesta": 0, "sin_respuesta": 0},
        "df_grafico_llamadas": pd.DataFrame(),
        "df_efectividad_call": pd.DataFrame(),
        "df_llamadas_por_dia": pd.DataFrame(),
        "alerta_umbral": 0,
        "df_funnel_mensajeria": pd.DataFrame(),
        "df_efectividad_mensajeria": pd.DataFrame(),
        "df_novedades_mapeadas": pd.DataFrame(),
        "df_agg_novedades_por_call": pd.DataFrame(),
        "df_agg_novedades_por_tipo": pd.DataFrame()
    }

# --- 2. Funciones Ayudantes: Procesamiento de Cartera y Reporte ---

def _clean_cartera_df(df: pd.DataFrame) -> pd.DataFrame:
    df['Estado_Pago'] = np.where(df['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO') if 'Total_Recaudo' in df.columns else 'SIN DATO'
    df['Estado_Gestion'] = np.where(df['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN') if 'Cantidad_Novedades' in df.columns else 'SIN DATO'

    columnas_numericas = ['Meta_General', 'Meta_$', 'Recaudo_Meta']
    for col in columnas_numericas:
        df[col] = pd.to_numeric(df.get(col), errors='coerce').fillna(0)

    columnas_texto = ['Zona', 'Cobrador', 'Call_Center_Apoyo', 'Nombre_Call_Center', 'Franja_Meta', 'Rodamiento', 'Estado_Gestion', 'Estado_Pago']
    for col in columnas_texto:
        df[col] = df.get(col, 'SIN DATO').astype(str).str.strip().str.upper().replace('NAN', 'SIN DATO')
        
    return df

def _merge_cartera_with_novedades(df_detalle: pd.DataFrame, df_novedades: pd.DataFrame) -> pd.DataFrame:
    if df_novedades.empty or 'Cedula_Cliente' not in df_novedades.columns:
        df_detalle['Tipo_Novedad'] = 'SIN NOVEDAD'
        df_detalle['Novedad'] = ''
        return df_detalle

    df_novedades_limpia = df_novedades.copy()
    df_novedades_limpia['Tipo_Novedad'] = df_novedades_limpia.get('Tipo_Novedad', 'N/A')
    df_novedades_limpia['Novedad'] = df_novedades_limpia.get('Novedad', 'N/A')
    
    # NOTA: Este merge puede duplicar filas si el cliente tiene múltiples novedades.
    # Por eso el cálculo de métricas de cartera (Rodamientos) debe hacerse ANTES de este paso.
    cols_to_merge = ['Cedula_Cliente', 'Tipo_Novedad', 'Novedad']
    df_novedades_detalle = df_novedades_limpia[cols_to_merge]
    
    df_detalle = df_detalle.merge(df_novedades_detalle, on='Cedula_Cliente', how='left')
    
    df_detalle['Tipo_Novedad'] = df_detalle['Tipo_Novedad'].fillna('SIN NOVEDAD').astype(str).str.strip().str.upper()
    df_detalle['Novedad'] = df_detalle['Novedad'].fillna('')
    return df_detalle

def _process_cartera_and_report(df_cartera: pd.DataFrame, df_novedades: pd.DataFrame) -> dict:
    """
    Procesa la cartera con lógica de CASCADA para asegurar que no se pierdan cuentas.
    1. Toma todo lo de ZONA que sea 'AL DIA'.
    2. Toma todo lo de APOYO que no haya sido tomado en el paso 1 (sin importar su franja).
    """
    df = _clean_cartera_df(df_cartera)
    
    # =========================================================================
    # 1. FILTRADO POR CASCADA (Para asegurar suma correcta)
    # =========================================================================
    
    # --- PASO 1: Identificar lo que pertenece a ZONA (Prioridad) ---
    # Condición: Estar en la lista de CLs en columna Zona Y estar AL DIA.
    mask_zona_al_dia = (
        (df['Zona'].isin(ALL_CALL_CENTERS)) & 
        (df['Franja_Meta'] == 'AL DIA')
    )
    df_zona = df[mask_zona_al_dia].copy()
    
    # --- PASO 2: Identificar lo que pertenece a APOYO (El resto) ---
    # Condición: Estar en la lista de CLs en columna Apoyo...
    # ... Y NO haber sido seleccionado ya en el paso 1.
    mask_apoyo_general = df['Call_Center_Apoyo'].isin(ALL_CALL_CENTERS)
    
    # Aquí está el cambio clave: En vez de preguntar si la franja es diferente a AL DIA,
    # simplemente preguntamos: "¿Es un Apoyo válido y NO es una cuenta que ya contamos en Zona?"
    # Esto atrapa las 34 cuentas sin importar qué franja tengan escrita.
    mask_apoyo_final = mask_apoyo_general & (~mask_zona_al_dia)
    
    df_apoyo = df[mask_apoyo_final].copy()

    # =========================================================================
    # 2. NORMALIZACIÓN DE COLUMNAS
    # =========================================================================
    
    # Normalizamos ZONA
    df_zona_norm = df_zona.rename(columns={
        'Zona': 'CALL_CENTER_ID',
        'Cobrador': 'NOMBRE_AGENTE',
        'Meta_General': 'META_UNIFICADA'
    })[['CALL_CENTER_ID', 'NOMBRE_AGENTE', 'META_UNIFICADA', 'Recaudo_Meta', 'Rodamiento', 'Cedula_Cliente']].copy()
    
    # Normalizamos APOYO
    df_apoyo_norm = df_apoyo.rename(columns={
        'Call_Center_Apoyo': 'CALL_CENTER_ID',
        'Nombre_Call_Center': 'NOMBRE_AGENTE',
        'Meta_$': 'META_UNIFICADA'
    })[['CALL_CENTER_ID', 'NOMBRE_AGENTE', 'META_UNIFICADA', 'Recaudo_Meta', 'Rodamiento', 'Cedula_Cliente']].copy()

    # =========================================================================
    # 3. UNIFICACIÓN
    # =========================================================================
    
    # Concatenamos para tener el UNIVERSO TOTAL de cuentas de Call Center
    df_total_unificado = pd.concat([df_zona_norm, df_apoyo_norm], ignore_index=True)
    
    # --- A) Reporte de Cumplimiento (Suma de Metas y Recaudos) ---
    agg_total = pd.DataFrame(columns=['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta', 'Franja'])
    
    if not df_total_unificado.empty:
        agg_total = df_total_unificado.groupby(['CALL_CENTER_ID', 'NOMBRE_AGENTE']).agg(
            Meta_Total=('META_UNIFICADA', 'sum'),
            Recaudo_Total=('Recaudo_Meta', 'sum')
        ).reset_index()
        
        agg_total.rename(columns={
            'CALL_CENTER_ID': 'CALL_CENTER', 
            'NOMBRE_AGENTE': 'NOMBRE', 
            'Meta_Total': 'META_$',
            'Recaudo_Total': 'Recaudo_Meta'
        }, inplace=True)
        
        agg_total['Franja'] = 'CONSOLIDADO' 

    reporte_raw = pd.DataFrame()
    if not agg_total.empty:
        agg_total['Faltante'] = agg_total['META_$'] - agg_total['Recaudo_Meta']
        agg_total['Cumplimiento'] = np.where(
            agg_total['META_$'] > 0, 
            agg_total['Recaudo_Meta'] / agg_total['META_$'], 
            0
        )
        columnas_finales_raw = ['CALL_CENTER', 'NOMBRE', 'Franja', 'META_$', 'Recaudo_Meta', 'Faltante', 'Cumplimiento']
        reporte_raw = agg_total[columnas_finales_raw].sort_values(by='CALL_CENTER').reset_index(drop=True)

    # --- B) Datos para Rodamiento (PIE CHART) ---
    # Al usar df_total_unificado, estamos garantizando que usamos las 114 de Zona + las 34 de Apoyo.
    agg_rodamiento = pd.DataFrame()
    if not df_total_unificado.empty and 'Rodamiento' in df_total_unificado.columns:
        # Usamos dropna=False por si acaso hay rodamientos vacíos que queremos contar
        agg_rodamiento = df_total_unificado.groupby('Rodamiento', dropna=False).size().reset_index(name='count')

    # =========================================================================
    # 4. DETALLE FINAL
    # =========================================================================
    # Reconstruimos la base única con las columnas originales para la tabla de detalle
    df_base_unica_raw = pd.concat([df_zona, df_apoyo], ignore_index=True)
    df_detalle_final = _merge_cartera_with_novedades(df_base_unica_raw, df_novedades)

    return {
        "reporte_raw": reporte_raw,
        "rodamiento_data": agg_rodamiento,
        "cartera_detallada_call_center": df_detalle_final,
        "df_cartera_procesada": df 
    }

# --- 3. Funciones Ayudantes: Procesamiento de Novedades por Call Center ---

def _normalize_name_set(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    
    def normalize_string(name):
        if not isinstance(name, str):
            return set()
        name = ''.join(
            c for c in unicodedata.normalize('NFD', name.lower())
            if unicodedata.category(c) != 'Mn'
        )
        return set(name.split())

    return series.apply(normalize_string)

def _process_novedades_por_call(df_novedades: pd.DataFrame, df_llamadas: pd.DataFrame) -> dict:
    default_return = {
        "df_novedades_mapeadas": pd.DataFrame(),
        "df_agg_novedades_por_call": pd.DataFrame(),
        "df_agg_novedades_por_tipo": pd.DataFrame(),
        "novedades_alert": None 
    }
    
    TARGET_ALERT_MESSAGE = "No hay suficientes datos para cruzar Novedades del Sistema con Call Centers (desde Llamadas)."

    if df_novedades.empty or df_llamadas.empty or \
       'Nombre_Usuario' not in df_novedades.columns or \
       'Nombre_Call' not in df_llamadas.columns or \
       'Call_Center_Limpio' not in df_llamadas.columns:
        
        default_return['novedades_alert'] = TARGET_ALERT_MESSAGE
        return default_return

    try:
        df_map = df_llamadas[['Nombre_Call', 'Call_Center_Limpio']].drop_duplicates().dropna()
        df_map['normalized_set'] = _normalize_name_set(df_map['Nombre_Call'])
        
        df_map['set_len'] = df_map['normalized_set'].apply(len)
        df_map = df_map[df_map['set_len'] > 0].sort_values(by='set_len', ascending=False)
        
        lookup_list = list(df_map[['normalized_set', 'Call_Center_Limpio']].itertuples(index=False, name=None))

        if not lookup_list:
            default_return['novedades_alert'] = "No se pudieron generar nombres de agentes desde el archivo de llamadas."
            return default_return

        df_nov = df_novedades.copy()
        df_nov['normalized_set_usuario'] = _normalize_name_set(df_nov['Nombre_Usuario'])

        def find_call_center_match(usuario_set):
            if not usuario_set:
                return 'SIN ASIGNAR'
            for lookup_set, call_center in lookup_list:
                if lookup_set.issubset(usuario_set):
                    return call_center
            return 'SIN ASIGNAR'

        df_nov['Call_Center_Mapeado'] = df_nov['normalized_set_usuario'].apply(find_call_center_match)
        
        df_agg_novedades_por_call = df_nov.groupby('Call_Center_Mapeado').size().reset_index(name='Total_Novedades')
        
        tipo_col = 'Tipo_Novedad' if 'Tipo_Novedad' in df_nov.columns else 'Novedad'
        if tipo_col not in df_nov.columns:
             df_nov[tipo_col] = 'N/A'
             
        df_agg_novedades_por_tipo = df_nov.groupby(['Call_Center_Mapeado', tipo_col]).size().reset_index(name='Total')
        
        return {
            "df_novedades_mapeadas": df_nov,
            "df_agg_novedades_por_call": df_agg_novedades_por_call,
            "df_agg_novedades_por_tipo": df_agg_novedades_por_tipo,
            "novedades_alert": None 
        }

    except Exception as e:
        default_return['novedades_alert'] = f"Error al procesar el cruce de novedades: {e}"
        return default_return

# --- FUNCIÓN PRINCIPAL (PÚBLICA) ---
def prepare_tab6_data(df_cartera_filtrada: pd.DataFrame, df_novedades_filtrada: pd.DataFrame, df_llamadas_filtrada: pd.DataFrame, df_mensajeria_filtrada: pd.DataFrame) -> dict: 
    if df_cartera_filtrada.empty:
        st.warning("No hay datos de cartera para procesar en el Tab 6.")
        return _handle_empty_input()
    
    # 1. Procesar Cartera
    cartera_data = _process_cartera_and_report(
        df_cartera_filtrada.copy(), 
        df_novedades_filtrada
    )
    
    # 2. Procesar Llamadas
    llamadas_data = process_llamadas(df_llamadas_filtrada.copy())
    
    # 3. Procesar Mensajería
    df_cartera_procesada = cartera_data["df_cartera_procesada"]
    mensajeria_data = process_mensajeria_funnel(
        df_mensajeria_filtrada.copy(), 
        df_novedades_filtrada, 
        df_cartera_procesada 
    )
    
    # 4. Procesar Novedades del Sistema
    novedades_sistema_data = process_novedades_system(
        df_novedades_filtrada.copy(),
        df_llamadas_filtrada.copy() 
    )

    final_data = {
        **cartera_data,
        **llamadas_data,
        **mensajeria_data,
        **novedades_sistema_data, 
        
        "df_llamadas_filtrada": df_llamadas_filtrada,
        "df_mensajeria_filtrada": df_mensajeria_filtrada, 
    }
    
    if "df_cartera_procesada" in final_data:
        del final_data["df_cartera_procesada"]
    
    return final_data