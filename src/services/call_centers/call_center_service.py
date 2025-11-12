# src/services/call_centers/call_center_service.py
import pandas as pd
import numpy as np
import streamlit as st
import unicodedata 

# --- [NUEVO] Importar los módulos de lógica específicos ---
from .sub_llamadas_service import process_llamadas
from .sub_mensajeria_service import process_mensajeria_funnel

# --- Constantes de Configuración ---
CALL_CENTERS_ZONA = ['CL1', 'CL2', 'CL3', 'CL4']
CALL_CENTERS_APOYO = ['CL5', 'CL6', 'CL7', 'CL8', 'CL9']

# --- 1. Función Ayudante: Datos Vacíos ---
def _handle_empty_input():
    """Retorna la estructura de diccionario por defecto si el input está vacío."""
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
# (Lógica omitida, asumiendo que es correcta)

def _clean_cartera_df(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y estandariza las columnas del DataFrame de cartera."""
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
    """Cruza el detalle de cartera con las novedades."""
    if df_novedades.empty or 'Cedula_Cliente' not in df_novedades.columns:
        df_detalle['Tipo_Novedad'] = 'SIN NOVEDAD'
        df_detalle['Novedad'] = ''
        return df_detalle

    df_novedades_limpia = df_novedades.copy()
    df_novedades_limpia['Tipo_Novedad'] = df_novedades_limpia.get('Tipo_Novedad', 'N/A')
    df_novedades_limpia['Novedad'] = df_novedades_limpia.get('Novedad', 'N/A')
    
    cols_to_merge = ['Cedula_Cliente', 'Tipo_Novedad', 'Novedad']
    df_novedades_detalle = df_novedades_limpia[cols_to_merge]
    
    df_detalle = df_detalle.merge(df_novedades_detalle, on='Cedula_Cliente', how='left')
    
    df_detalle['Tipo_Novedad'] = df_detalle['Tipo_Novedad'].fillna('SIN NOVEDAD').astype(str).str.strip().str.upper()
    df_detalle['Novedad'] = df_detalle['Novedad'].fillna('')
    return df_detalle

def _process_cartera_and_report(df_cartera: pd.DataFrame, df_novedades: pd.DataFrame) -> dict:
    """
    Procesa la cartera, genera el reporte raw y los datos de rodamiento.
    """
    df = _clean_cartera_df(df_cartera)
    
    # 1. Crear Detalle Call Centers y cruzar con Novedades
    df_detalle_call_centers = df[
        df['Zona'].isin(CALL_CENTERS_ZONA) | df['Call_Center_Apoyo'].isin(CALL_CENTERS_APOYO)
    ].copy()
    df_detalle_call_centers = _merge_cartera_with_novedades(df_detalle_call_centers, df_novedades)

    # 2. Generar Reporte Raw (agregaciones)
    df_cl1_4 = df[(df['Zona'].isin(CALL_CENTERS_ZONA)) & (df['Franja_Meta'] == 'AL DIA')]
    agg_cl1_4 = pd.DataFrame(columns=['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta'])
    if not df_cl1_4.empty:
        agg_cl1_4 = df_cl1_4.groupby(['Zona', 'Cobrador']).agg(
            Meta_General=('Meta_General', 'sum'),
            Recaudo_Meta=('Recaudo_Meta', 'sum')
        ).reset_index()
        agg_cl1_4.rename(columns={'Zona': 'CALL_CENTER', 'Cobrador': 'NOMBRE', 'Meta_General': 'META_$'}, inplace=True)

    df_cl5_9 = df[df['Call_Center_Apoyo'].isin(CALL_CENTERS_APOYO)]
    agg_cl5_9 = pd.DataFrame(columns=['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta'])
    if not df_cl5_9.empty:
        agg_cl5_9 = df_cl5_9.groupby(['Call_Center_Apoyo', 'Nombre_Call_Center']).agg(
            Meta_Dollar=('Meta_$', 'sum'),
            Recaudo_Meta=('Recaudo_Meta', 'sum')
        ).reset_index()
        agg_cl5_9.rename(columns={'Call_Center_Apoyo': 'CALL_CENTER', 'Nombre_Call_Center': 'NOMBRE', 'Meta_Dollar': 'META_$'}, inplace=True)

    df_reporte = pd.concat([agg_cl1_4, agg_cl5_9], ignore_index=True)
    reporte_raw = pd.DataFrame()
    if not df_reporte.empty:
        df_reporte['Faltante'] = df_reporte['META_$'] - df_reporte['Recaudo_Meta']
        df_reporte['Cumplimiento'] = np.where(df_reporte['META_$'] > 0, df_reporte['Recaudo_Meta'] / df_reporte['META_$'], 0)
        columnas_finales_raw = ['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta', 'Faltante', 'Cumplimiento']
        reporte_raw = df_reporte[columnas_finales_raw].sort_values(by='CALL_CENTER').reset_index(drop=True)

    # 3. Datos de Rodamiento
    agg_rodamiento = pd.DataFrame() 
    if not df_detalle_call_centers.empty and 'Rodamiento' in df_detalle_call_centers.columns:
        agg_rodamiento = df_detalle_call_centers.groupby('Rodamiento').size().reset_index(name='count')
        
    return {
        "reporte_raw": reporte_raw,
        "rodamiento_data": agg_rodamiento,
        "cartera_detallada_call_center": df_detalle_call_centers,
        "df_cartera_procesada": df # Devolver el DF limpio para el funnel
    }

# --- 3. Funciones Ayudantes: Procesamiento de Novedades por Call Center ---
# (Esta lógica se queda aquí ya que depende de las otras)

def _normalize_name_set(series: pd.Series) -> pd.Series:
    """
    Normaliza una serie de nombres a un conjunto de palabras clave.
    Ej: 'Kelly Mejía Daza' -> {'kelly', 'mejia', 'daza'}
    """
    if series.empty:
        return series
    
    def normalize_string(name):
        if not isinstance(name, str):
            return set()
        # 1. Minúsculas y quitar acentos
        name = ''.join(
            c for c in unicodedata.normalize('NFD', name.lower())
            if unicodedata.category(c) != 'Mn'
        )
        # 2. Dividir en palabras y convertir a set
        return set(name.split())

    return series.apply(normalize_string)

def _process_novedades_por_call(df_novedades: pd.DataFrame, df_llamadas: pd.DataFrame) -> dict:
    """
    Asocia las novedades del sistema con los call centers basándose en el
    nombre del agente de LLAMADAS ('Nombre_Call') y el usuario de 
    novedades ('Nombre_Usuario').
    """
    # Diccionario de retorno por defecto
    default_return = {
        "df_novedades_mapeadas": pd.DataFrame(),
        "df_agg_novedades_por_call": pd.DataFrame(),
        "df_agg_novedades_por_tipo": pd.DataFrame(),
        "novedades_alert": None # NUEVA CLAVE PARA ALERTA
    }
    
    TARGET_ALERT_MESSAGE = "No hay suficientes datos para cruzar Novedades del Sistema con Call Centers (desde Llamadas)."

    # Validar DFs y columnas necesarias
    if df_novedades.empty or df_llamadas.empty or \
       'Nombre_Usuario' not in df_novedades.columns or \
       'Nombre_Call' not in df_llamadas.columns or \
       'Call_Center_Limpio' not in df_llamadas.columns:
        
        # CAMBIO CLAVE: NO llamamos a st.info(). Devolvemos la alerta.
        default_return['novedades_alert'] = TARGET_ALERT_MESSAGE
        return default_return

    try:
        # --- Paso 1: Crear el mapa de búsqueda desde Llamadas ---
        df_map = df_llamadas[['Nombre_Call', 'Call_Center_Limpio']].drop_duplicates().dropna()
        df_map['normalized_set'] = _normalize_name_set(df_map['Nombre_Call'])
        
        df_map['set_len'] = df_map['normalized_set'].apply(len)
        df_map = df_map[df_map['set_len'] > 0].sort_values(by='set_len', ascending=False)
        
        lookup_list = list(df_map[['normalized_set', 'Call_Center_Limpio']].itertuples(index=False, name=None))

        if not lookup_list:
            # CAMBIO CLAVE: Devolvemos la alerta si no hay mapa de agentes
            default_return['novedades_alert'] = "No se pudieron generar nombres de agentes desde el archivo de llamadas."
            return default_return

        # --- Paso 2: Normalizar y Mapear Novedades ---
        df_nov = df_novedades.copy()
        df_nov['normalized_set_usuario'] = _normalize_name_set(df_nov['Nombre_Usuario'])

        # --- Paso 3: Función de Mapeo por Subconjunto (Subset) ---
        def find_call_center_match(usuario_set):
            if not usuario_set:
                return 'SIN ASIGNAR'
            for lookup_set, call_center in lookup_list:
                if lookup_set.issubset(usuario_set):
                    return call_center
            return 'SIN ASIGNAR'

        # Aplicar la función de mapeo
        df_nov['Call_Center_Mapeado'] = df_nov['normalized_set_usuario'].apply(find_call_center_match)
        
        # --- Paso 4: Agregar los datos para los gráficos ---
        df_agg_novedades_por_call = df_nov.groupby('Call_Center_Mapeado').size().reset_index(name='Total_Novedades')
        
        tipo_col = 'Tipo_Novedad' if 'Tipo_Novedad' in df_nov.columns else 'Novedad'
        if tipo_col not in df_nov.columns:
             df_nov[tipo_col] = 'N/A'
             
        df_agg_novedades_por_tipo = df_nov.groupby(['Call_Center_Mapeado', tipo_col]).size().reset_index(name='Total')
        
        return {
            "df_novedades_mapeadas": df_nov,
            "df_agg_novedades_por_call": df_agg_novedades_por_call,
            "df_agg_novedades_por_tipo": df_agg_novedades_por_tipo,
            "novedades_alert": None # Éxito, no hay alerta
        }

    except Exception as e:
        st.error(f"Error al procesar el cruce de novedades y llamadas: {e}")
        default_return['novedades_alert'] = f"Error al procesar el cruce de novedades: {e}"
        return default_return


# --- FUNCIÓN PRINCIPAL (PÚBLICA) ---

def prepare_tab6_data(df_cartera_filtrada: pd.DataFrame, df_novedades_filtrada: pd.DataFrame, df_llamadas_filtrada: pd.DataFrame, df_mensajeria_filtrada: pd.DataFrame) -> dict: 
    """
    Prepara los datos para el reporte de Call Centers en el Tab 6.
    Esta función coordina a funciones ayudantes para procesar cada sección.
    """
    
    # --- 0. Validación de Entrada ---
    if df_cartera_filtrada.empty:
        st.warning("No hay datos de cartera para procesar en el Tab 6.")
        return _handle_empty_input()
    
    # --- 1. Procesar Cartera, Reporte Raw y Detalles ---
    cartera_data = _process_cartera_and_report(
        df_cartera_filtrada.copy(), 
        df_novedades_filtrada
    )
    
    # --- 2. Procesar Llamadas (Llama al módulo importado) ---
    llamadas_data = process_llamadas(df_llamadas_filtrada.copy())
    
    # --- 3. Procesar Mensajería y Funnel (Llama al módulo importado) ---
    df_cartera_procesada = cartera_data["df_cartera_procesada"]
    
    mensajeria_data = process_mensajeria_funnel(
        df_mensajeria_filtrada.copy(), 
        df_novedades_filtrada, 
        df_cartera_procesada 
    )
    
    # --- 4. Procesar Novedades del Sistema por Call Center ---
    novedades_sistema_data = _process_novedades_por_call(
        df_novedades_filtrada.copy(),
        df_llamadas_filtrada.copy() 
    )

    # --- 5. Ensamblar el diccionario final ---
    final_data = {
        **cartera_data,
        **llamadas_data,
        **mensajeria_data,
        **novedades_sistema_data,
        
        # Pasar los DFs originales filtrados (que las sub-tabs esperan)
        "df_llamadas_filtrada": df_llamadas_filtrada,
        "df_mensajeria_filtrada": df_mensajeria_filtrada, 
    }
    
    # Limpiar: remover la cartera procesada temporal que no se retorna
    if "df_cartera_procesada" in final_data:
        del final_data["df_cartera_procesada"]
    
    return final_data