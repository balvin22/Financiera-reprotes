import pandas as pd
import numpy as np
import streamlit as st
import unicodedata

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
        # [NUEVO] Añadir los DFs para el nuevo subtab
        "df_novedades_mapeadas": pd.DataFrame(),
        "df_agg_novedades_por_call": pd.DataFrame(),
        "df_agg_novedades_por_tipo": pd.DataFrame()
    }

# --- 2. Funciones Ayudantes: Procesamiento de Cartera y Reporte ---
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

# --- 3. Funciones Ayudantes: Procesamiento de Llamadas ---
# ... (Las funciones _calculate_llamadas_por_dia y _process_llamadas no cambian) ...
def _calculate_llamadas_por_dia(df_llamadas_limpio: pd.DataFrame) -> pd.DataFrame:
    """Calcula la tendencia de llamadas por día, excluyendo fines de semana."""
    if 'Fecha_Llamada' not in df_llamadas_limpio.columns:
        st.warning("No se encontró la columna 'Fecha_Llamada' para el gráfico de tendencia.")
        return pd.DataFrame()
    try:
        df_temp = df_llamadas_limpio.copy()
        df_temp['Fecha_Dia'] = pd.to_datetime(df_temp['Fecha_Llamada']).dt.date
        
        # Excluir fines de semana (Sábado=5, Domingo=6)
        dias_semana = pd.to_datetime(df_temp['Fecha_Dia']).dt.dayofweek
        df_llamadas_habiles = df_temp[~dias_semana.isin([5, 6])].copy()
        
        if df_llamadas_habiles.empty:
            st.info("No se encontraron registros de llamadas en días hábiles para la tendencia.")
            return pd.DataFrame()
            
        df_llamadas_habiles['Estado_Respuesta'] = np.where(
            df_llamadas_habiles['Estado_Llamada'] == 'ANSWERED', 'CON RESPUESTA', 'SIN RESPUESTA'
        )
        
        df_llamadas_dia_agg = df_llamadas_habiles.groupby(['Fecha_Dia', 'Estado_Respuesta']).size().reset_index(name='Total_Llamadas')
        df_llamadas_dia_agg.rename(columns={'Fecha_Dia': 'Fecha'}, inplace=True)
        return df_llamadas_dia_agg
    except Exception as e:
        st.warning(f"Error procesando fechas para gráfico de llamadas por día: {e}")
        return pd.DataFrame()

def _process_llamadas(df_llamadas: pd.DataFrame) -> dict:
    """Procesa todas las estadísticas y DFs relacionados con las llamadas."""
    if df_llamadas.empty or 'Estado_Llamada' not in df_llamadas.columns:
        return {
            "llamadas_stats": {"total_llamadas": 0, "con_respuesta": 0, "sin_respuesta": 0},
            "df_grafico_llamadas": pd.DataFrame({"Tipo": ["CON RESPUESTA", "SIN RESPUESTA"], "Cantidad": [0, 0]}),
            "df_efectividad_call": pd.DataFrame(),
            "df_llamadas_por_dia": pd.DataFrame(),
            "alerta_umbral": 0
        }

    df_llamadas_limpio = df_llamadas.copy()
    df_llamadas_limpio['Estado_Llamada'] = df_llamadas_limpio['Estado_Llamada'].astype(str).str.strip().str.upper()
    
    total_llamadas = len(df_llamadas_limpio)
    con_respuesta = len(df_llamadas_limpio[df_llamadas_limpio['Estado_Llamada'] == 'ANSWERED'])
    sin_respuesta = total_llamadas - con_respuesta
    
    llamadas_stats = {
        "total_llamadas": total_llamadas,
        "con_respuesta": con_respuesta,
        "sin_respuesta": sin_respuesta
    }
    
    df_grafico_llamadas = pd.DataFrame({
        "Tipo": ["CON RESPUESTA", "SIN RESPUESTA"],
        "Cantidad": [con_respuesta, sin_respuesta]
    })
    
    df_efectividad_call = pd.DataFrame()
    try:
        # Asumiendo que 'Call_Center_Limpio' existe tras el filtrado
        agg_calls = df_llamadas_limpio.groupby('Call_Center_Limpio').agg(
            Total_Intentos=('Estado_Llamada', 'size'),
            Con_Respuesta=('Estado_Llamada', lambda x: (x == 'ANSWERED').sum())
        ).reset_index()
        agg_calls['Efectividad'] = np.where(agg_calls['Total_Intentos'] > 0, agg_calls['Con_Respuesta'] / agg_calls['Total_Intentos'], 0)
        agg_calls.rename(columns={'Call_Center_Limpio': 'Call_Center'}, inplace=True)
        df_efectividad_call = agg_calls.sort_values(by='Efectividad', ascending=False)
    except Exception as e:
        st.error(f"Error calculando efectividad de llamadas: {e}")
        df_efectividad_call = pd.DataFrame()

    alerta_umbral = 0
    if 'Call_Center_Limpio' in df_llamadas_limpio.columns:
        n_call_centers = df_llamadas_limpio['Call_Center_Limpio'].nunique()
        if n_call_centers > 0:
            alerta_umbral = n_call_centers * 30
            
    df_llamadas_por_dia = _calculate_llamadas_por_dia(df_llamadas_limpio)
    
    return {
        "llamadas_stats": llamadas_stats,
        "df_grafico_llamadas": df_grafico_llamadas,
        "df_efectividad_call": df_efectividad_call,
        "df_llamadas_por_dia": df_llamadas_por_dia,
        "alerta_umbral": alerta_umbral
    }


# --- 4. Funciones Ayudantes: Procesamiento de Mensajería y Funnel ---
# ... (Las funciones _normalize_telefonos y _process_mensajeria_funnel no cambian) ...
def _normalize_telefonos(series: pd.Series) -> pd.Series:
    """Normaliza una serie de teléfonos a string, quitando nulos y '.0'."""
    return series.dropna().astype(str).str.replace(r'\.0$', '', regex=True)

def _process_mensajeria_funnel(df_mensajeria: pd.DataFrame, df_novedades: pd.DataFrame, df_cartera: pd.DataFrame) -> dict:
    """Procesa el embudo de conversión de mensajería y la efectividad."""
    if df_mensajeria.empty or df_novedades.empty or df_cartera.empty:
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}

    try:
        # --- Paso 1 y 2: Entregados, Conversaciones y Efectividad ---
        df_mensajeria_limpio = df_mensajeria.copy()
        total_mensajes = len(df_mensajeria_limpio)
        total_conversaciones = 0
        df_conversaciones = pd.DataFrame()
        df_efectividad_mensajeria = pd.DataFrame()

        if 'Primer_Mensaje_Agente' in df_mensajeria_limpio.columns:
            df_mensajeria_limpio['Primer_Mensaje_Agente'] = df_mensajeria_limpio['Primer_Mensaje_Agente'].astype(str).replace('nan', '')
            df_mensajeria_limpio['Es_Conversacion'] = np.where(
                df_mensajeria_limpio['Primer_Mensaje_Agente'].notna() &
                (df_mensajeria_limpio['Primer_Mensaje_Agente'] != '') &
                (df_mensajeria_limpio['Primer_Mensaje_Agente'] != 'None'), 1, 0
            )
            df_conversaciones = df_mensajeria_limpio[df_mensajeria_limpio['Es_Conversacion'] == 1].copy()
            total_conversaciones = len(df_conversaciones)
        else:
            st.warning("Columna 'Primer_Mensaje_Agente' no encontrada en datos de mensajería.")

        if 'Call_Center' in df_mensajeria_limpio.columns:
            agg_msgs = df_mensajeria_limpio.groupby('Call_Center').agg(
                Total_Entregados=('Primer_Mensaje_Agente', 'size'),
                Total_Conversaciones=('Es_Conversacion', 'sum')
            ).reset_index()
            agg_msgs['Efectividad'] = np.where(agg_msgs['Total_Entregados'] > 0, agg_msgs['Total_Conversaciones'] / agg_msgs['Total_Entregados'], 0)
            df_efectividad_mensajeria = agg_msgs.sort_values(by='Efectividad', ascending=False)
        else:
            st.warning("Columna 'Call_Center' no encontrada en datos de mensajería para gráfico de efectividad.")
            
        # --- Paso 3: Gestion en Sistema ---
        total_gestion_sistema = 0
        df_gestion_sistema = pd.DataFrame()
        if not df_conversaciones.empty and 'Numero_Telefono' in df_conversaciones.columns:
            telefonos_novedades = set(_normalize_telefonos(df_novedades.get('Telefono_Cliente', pd.Series(dtype=str))))
            telefonos_novedades.update(_normalize_telefonos(df_novedades.get('Celular_Cliente', pd.Series(dtype=str))))
            
            if not telefonos_novedades:
                st.warning("No se encontraron teléfonos en 'Detalle_Novedades' para cruzar.")
            else:
                df_conversaciones['Numero_Telefono_Norm'] = _normalize_telefonos(df_conversaciones['Numero_Telefono'])
                df_gestion_sistema = df_conversaciones[df_conversaciones['Numero_Telefono_Norm'].isin(telefonos_novedades)].copy()
                total_gestion_sistema = len(df_gestion_sistema)

        # --- Paso 4: Clientes con Pago ---
        total_clientes_pago = 0
        if not df_gestion_sistema.empty:
            cedulas_con_pago = set(df_cartera[df_cartera['Estado_Pago'] == 'PAGO']['Cedula_Cliente'].dropna().astype(str))
            
            if cedulas_con_pago:
                map_tel_a_cedula = {}
                df_novedades_map = df_novedades.dropna(subset=['Cedula_Cliente']).copy()
                
                if 'Telefono_Cliente' in df_novedades_map.columns:
                    df_novedades_map['Telefono_Cliente_Norm'] = _normalize_telefonos(df_novedades_map['Telefono_Cliente'])
                    map1 = df_novedades_map.set_index('Telefono_Cliente_Norm')['Cedula_Cliente'].astype(str).to_dict()
                    map_tel_a_cedula.update(map1)
                
                if 'Celular_Cliente' in df_novedades_map.columns:
                    df_novedades_map['Celular_Cliente_Norm'] = _normalize_telefonos(df_novedades_map['Celular_Cliente'])
                    map2 = df_novedades_map.set_index('Celular_Cliente_Norm')['Cedula_Cliente'].astype(str).to_dict()
                    map_tel_a_cedula.update(map2)

                if map_tel_a_cedula:
                    df_gestion_sistema['Cedula_Mapeada'] = df_gestion_sistema['Numero_Telefono_Norm'].map(map_tel_a_cedula)
                    total_clientes_pago = df_gestion_sistema['Cedula_Mapeada'].isin(cedulas_con_pago).sum()

        data_funnel = {
            'Etapa': ['Mensajes Entregados', 'Conversaciones', 'Gestion en Sistema', 'Clientes con Pago'],
            'Cantidad': [total_mensajes, total_conversaciones, total_gestion_sistema, total_clientes_pago]
        }
        df_funnel_mensajeria = pd.DataFrame(data_funnel)

    except Exception as e:
        st.error(f"Error al procesar el embudo de mensajería: {e}")
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}
    
    return {
        "df_funnel_mensajeria": df_funnel_mensajeria,
        "df_efectividad_mensajeria": df_efectividad_mensajeria
    }

# --- 5. [NUEVO] Funciones Ayudantes: Procesamiento de Novedades por Call Center ---

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

def _process_novedades_por_call(df_novedades: pd.DataFrame, df_mensajeria: pd.DataFrame) -> dict:
    """
    Asocia las novedades del sistema con los call centers basándose en el
    nombre del agente de mensajería ('Nombre_Call') y el usuario de 
    novedades ('Nombre_Usuario').
    """
    # Diccionario de retorno por defecto
    default_return = {
        "df_novedades_mapeadas": pd.DataFrame(),
        "df_agg_novedades_por_call": pd.DataFrame(),
        "df_agg_novedades_por_tipo": pd.DataFrame()
    }

    # Validar DFs y columnas necesarias
    if df_novedades.empty or df_mensajeria.empty or \
       'Nombre_Usuario' not in df_novedades.columns or \
       'Nombre_Call' not in df_mensajeria.columns or \
       'Call_Center' not in df_mensajeria.columns:
        
        st.info("No hay suficientes datos para cruzar Novedades del Sistema con Call Centers.")
        return default_return

    try:
        # --- Paso 1: Crear el mapa de búsqueda desde Mensajería ---
        # (Nombre_Call, Call_Center)
        df_map = df_mensajeria[['Nombre_Call', 'Call_Center']].drop_duplicates().dropna()
        
        # Normalizar los nombres de 'Nombre_Call' a un set de palabras
        df_map['normalized_set'] = _normalize_name_set(df_map['Nombre_Call'])
        
        # Filtrar los que no tienen nombre y crear la lista de búsqueda
        # (Se ordena por la longitud del set, de más largo a más corto,
        # para que 'Kelly Johana' coincida antes que 'Kelly' a secas)
        df_map['set_len'] = df_map['normalized_set'].apply(len)
        df_map = df_map[df_map['set_len'] > 0].sort_values(by='set_len', ascending=False)
        
        lookup_list = list(df_map[['normalized_set', 'Call_Center']].itertuples(index=False, name=None))

        if not lookup_list:
            st.warning("No se pudieron generar nombres de agentes desde el archivo de mensajería.")
            return default_return

        # --- Paso 2: Normalizar y Mapear Novedades ---
        df_nov = df_novedades.copy()
        df_nov['normalized_set_usuario'] = _normalize_name_set(df_nov['Nombre_Usuario'])

        # --- Paso 3: Función de Mapeo por Subconjunto (Subset) ---
        def find_call_center_match(usuario_set):
            if not usuario_set:
                return 'SIN ASIGNAR'
            # Buscar el primer agente (lookup_set) que esté
            # COMPLETAMENTE contenido en el nombre del usuario
            for lookup_set, call_center in lookup_list:
                if lookup_set.issubset(usuario_set):
                    return call_center
            return 'SIN ASIGNAR'

        # Aplicar la función de mapeo
        df_nov['Call_Center_Mapeado'] = df_nov['normalized_set_usuario'].apply(find_call_center_match)
        
        # --- Paso 4: Agregar los datos para los gráficos ---
        df_agg_novedades_por_call = df_nov.groupby('Call_Center_Mapeado').size().reset_index(name='Total_Novedades')
        
        # Agregación para el segundo gráfico (por tipo de novedad)
        tipo_col = 'Tipo_Novedad' if 'Tipo_Novedad' in df_nov.columns else 'Novedad'
        if tipo_col not in df_nov.columns:
             df_nov[tipo_col] = 'N/A'
             
        df_agg_novedades_por_tipo = df_nov.groupby(['Call_Center_Mapeado', tipo_col]).size().reset_index(name='Total')
        
        return {
            "df_novedades_mapeadas": df_nov,
            "df_agg_novedades_por_call": df_agg_novedades_por_call,
            "df_agg_novedades_por_tipo": df_agg_novedades_por_tipo
        }

    except Exception as e:
        st.error(f"Error al procesar el cruce de novedades y mensajería: {e}")
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
    
    # --- 2. Procesar Llamadas ---
    llamadas_data = _process_llamadas(df_llamadas_filtrada.copy())
    
    # --- 3. Procesar Mensajería y Funnel ---
    df_cartera_procesada = cartera_data["df_cartera_procesada"]
    
    mensajeria_data = _process_mensajeria_funnel(
        df_mensajeria_filtrada.copy(), 
        df_novedades_filtrada, 
        df_cartera_procesada 
    )
    
    # --- 4. [NUEVO] Procesar Novedades del Sistema por Call Center ---
    novedades_sistema_data = _process_novedades_por_call(
        df_novedades_filtrada.copy(),
        df_mensajeria_filtrada.copy()
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