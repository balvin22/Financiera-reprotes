# data_processing.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from config import ORDEN_FRANJAS, ZONA_COBRO_MAP

@st.cache_data
def prepare_tab1_data(df):
    """
    Toma el dataframe filtrado y realiza todas las agregaciones
    necesarias para los gráficos del Tab 1 de una sola vez.
    El resultado se guarda en caché para un rendimiento máximo.
    """
    if df.empty:
        return {}

    # --- 1. Datos para: create_regional_bar_chart ---
    agg_regional = df.groupby(['Regional_Venta', 'Franja_Meta']).size().reset_index(name='count')
    agg_regional['Franja_Meta'] = pd.Categorical(agg_regional['Franja_Meta'], categories=ORDEN_FRANJAS, ordered=True)
    agg_regional = agg_regional.sort_values('Franja_Meta')

    # --- 2. Datos para: create_cobro_bar_chart ---
    agg_cobro = None
    if 'Regional_Cobro' in df.columns and 'Zona_Cobro' in df.columns:
        df_cobro_copy = df[['Regional_Cobro', 'Zona_Cobro', 'Franja_Meta']].copy()
        mapped_zonas = df_cobro_copy['Zona_Cobro'].map(ZONA_COBRO_MAP)
        df_cobro_copy['Regional_Cobro'] = df_cobro_copy['Regional_Cobro'].replace('nan', np.nan)
        df_cobro_copy['Eje_X_Cobro'] = df_cobro_copy['Regional_Cobro'].fillna(mapped_zonas)
        df_cobro_copy.dropna(subset=['Eje_X_Cobro'], inplace=True)
        
        if not df_cobro_copy.empty:
            agg_cobro = df_cobro_copy.groupby(['Eje_X_Cobro', 'Franja_Meta']).size().reset_index(name='count')
            agg_cobro['Franja_Meta'] = pd.Categorical(agg_cobro['Franja_Meta'], categories=ORDEN_FRANJAS, ordered=True)
            agg_cobro = agg_cobro.sort_values('Franja_Meta')

    # --- 3. Datos para: create_desembolso_por_ano_chart ---
    agg_desembolso = None
    if 'Fecha_Desembolso' in df.columns and 'Valor_Desembolso' in df.columns:
        df_desembolso_copy = df[['Fecha_Desembolso', 'Franja_Meta', 'Valor_Desembolso']].copy()
        df_desembolso_copy['Fecha_Desembolso'] = pd.to_datetime(df_desembolso_copy['Fecha_Desembolso'], errors='coerce')
        df_desembolso_copy.dropna(subset=['Fecha_Desembolso'], inplace=True)
        df_desembolso_copy['Año_Desembolso'] = df_desembolso_copy['Fecha_Desembolso'].dt.year
        
        start_year, end_year = 2018, datetime.now().year
        df_desembolso_copy = df_desembolso_copy[df_desembolso_copy['Año_Desembolso'].between(start_year, end_year)]

        if not df_desembolso_copy.empty:
            agg_desembolso = df_desembolso_copy.groupby(['Año_Desembolso', 'Franja_Meta'])['Valor_Desembolso'].sum().reset_index()
            agg_desembolso.sort_values('Año_Desembolso', inplace=True)
            agg_desembolso['Franja_Meta'] = pd.Categorical(agg_desembolso['Franja_Meta'], categories=ORDEN_FRANJAS, ordered=True)

    # --- 4. Datos para: create_vigencia_sunburst_chart ---
    agg_vigencia = None
    if 'Fecha_Cuota_Vigente' in df.columns:
        df_vigencia_copy = df[['Fecha_Cuota_Vigente']].copy()
        fechas_reales = pd.to_datetime(df_vigencia_copy['Fecha_Cuota_Vigente'], errors='coerce')
        
        df_vigencia_copy['Estado_Vigencia_Agrupado'] = 'VIGENTES'
        df_vigencia_copy.loc[fechas_reales.isna(), 'Estado_Vigencia_Agrupado'] = df_vigencia_copy['Fecha_Cuota_Vigente']

        df_vigencia_copy['Sub_Estado_Vigencia'] = ''
        vigentes_mask = df_vigencia_copy['Estado_Vigencia_Agrupado'] == 'VIGENTES'
    
        if vigentes_mask.any():
            fechas_vigentes = fechas_reales[vigentes_mask]
            subdivision_labels = fechas_vigentes.dt.day.apply(lambda d: f"Día {d}")
            df_vigencia_copy.loc[vigentes_mask, 'Sub_Estado_Vigencia'] = subdivision_labels

        agg_vigencia = df_vigencia_copy.groupby(['Estado_Vigencia_Agrupado', 'Sub_Estado_Vigencia']).size().reset_index(name='count')

    return {
        "regional": agg_regional,
        "cobro": agg_cobro,
        "desembolso": agg_desembolso,
        "vigencia": agg_vigencia,
    }
    
@st.cache_data
def prepare_tab2_data(df_cartera, df_novedades):
    """
    Prepara y cachea todos los datos necesarios para los gráficos y la tabla del Tab 2.
    """
    if df_cartera.empty:
        return {}
    df_cartera = df_cartera[df_cartera['Valor_Cuota_Vigente'] != 'ANTICIPADO'].copy()
    if df_cartera.empty:
        return {}

    df_cartera['Estado_Pago'] = np.where(df_cartera['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
    cargos_unicos_por_cliente = df_novedades[['Cedula_Cliente', 'Cargo_Usuario']].drop_duplicates()
    agg_donut = df_cartera['Estado_Pago'].value_counts()

    df_cartera['Estado_Gestion'] = np.where(df_cartera['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')
    cargos_unicos_por_cliente = df_novedades[['Cedula_Cliente', 'Cargo_Usuario']].drop_duplicates()
    df_merged = pd.merge(df_cartera, cargos_unicos_por_cliente, on='Cedula_Cliente', how='left')
    df_merged['Cargo_Usuario'] = df_merged['Cargo_Usuario'].fillna('')
    
    grouped_sunburst_inicial = df_merged.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped_sunburst_inicial = grouped_sunburst_inicial[~((grouped_sunburst_inicial['Estado_Gestion'] == 'CON GESTIÓN') & (grouped_sunburst_inicial['Cargo_Usuario'] == ''))]
    conteo_gestion_inicial = df_merged['Estado_Gestion'].value_counts()
    agg_rodamiento = None
    if 'Rodamiento' in df_cartera.columns and 'Estado_Gestion' in df_cartera.columns:
        agg_rodamiento = df_cartera.groupby(['Rodamiento', 'Estado_Gestion']).size().reset_index(name='Número de Cuentas')
        
    df_pago = df_merged[df_merged['Estado_Pago'] == 'PAGO']
    df_sin_pago = df_merged[df_merged['Estado_Pago'] == 'SIN PAGO']

    grouped_detalle_pago = df_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    conteo_detalle_pago = df_pago['Estado_Gestion'].value_counts()
    
    grouped_detalle_sin_pago = df_sin_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    conteo_detalle_sin_pago = df_sin_pago['Estado_Gestion'].value_counts()

    # --- INICIO DE LA MODIFICACIÓN ---
    if not df_novedades.empty:
        # 1. Calcular el conteo de novedades por cargo (como antes)
        novedades_por_cargo_cliente = df_novedades.groupby(
            ['Cedula_Cliente', 'Cargo_Usuario']
        ).size().reset_index(name='Novedades_Por_Cargo')
        
        # 2. Unir el conteo a df_merged (que está a nivel Credito/Cargo)
        df_con_conteo = pd.merge(
            df_merged,
            novedades_por_cargo_cliente,
            on=['Cedula_Cliente', 'Cargo_Usuario'],
            how='left'
        )
        df_con_conteo['Novedades_Por_Cargo'] = df_con_conteo['Novedades_Por_Cargo'].fillna(0).astype(int)

        # 3. Preparar las columnas de detalle de novedades
        cols_detalle = ['Cedula_Cliente', 'Cargo_Usuario']
        
        # Añadir 'Novedad' si existe, si no, crear una columna para el merge
        if 'Novedad' not in df_novedades.columns:
            df_novedades['Novedad'] = 'N/A'
        cols_detalle.append('Novedad')

        # Añadir 'Tipo_Novedad' si existe, si no, crear una columna para el merge
        if 'Tipo_Novedad' not in df_novedades.columns:
            df_novedades['Tipo_Novedad'] = 'N/A'
        cols_detalle.append('Tipo_Novedad')

        # 4. Unir los detalles de CADA novedad. Esto expandirá el DataFrame.
        df_para_tabla = pd.merge(
            df_con_conteo,
            df_novedades[cols_detalle], 
            on=['Cedula_Cliente', 'Cargo_Usuario'],
            how='left' 
        )
        
        df_para_tabla['Novedad'] = df_para_tabla['Novedad'].fillna('')
        df_para_tabla['Tipo_Novedad'] = df_para_tabla['Tipo_Novedad'].fillna('')

    else:
    
        df_para_tabla = df_merged.copy()
        df_para_tabla['Novedades_Por_Cargo'] = 0
        df_para_tabla['Novedad'] = ''
        df_para_tabla['Tipo_Novedad'] = ''
    

    return {
        "donut_data": agg_donut,
        "sunburst_initial_grouped": grouped_sunburst_inicial,
        "sunburst_initial_counts": conteo_gestion_inicial,
        "rodamiento_data": agg_rodamiento,
        "detalle_pago": (grouped_detalle_pago, conteo_detalle_pago),
        "detalle_sin_pago": (grouped_detalle_sin_pago, conteo_detalle_sin_pago),
        "processed_cartera": df_cartera,
        "processed_data_merged": df_merged, 
        "data_para_tabla": df_para_tabla # Esta es la tabla ahora expandida
    }

@st.cache_data
def prepare_tab3_data(df):
    """
    Toma el dataframe filtrado globalmente y realiza la agregación principal
    por Zona y Franja_Meta y ahora por Cobrador para el Tab de Resultados.
    """

    franjas_a_usar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']    
    df_para_grupo = df[df['Franja_Meta'].isin(franjas_a_usar)]
    
    zonas_a_excluir = ['CL1', 'CL2', 'CL3', 'CL4']
    df_para_grupo = df_para_grupo[~df_para_grupo['Zona'].isin(zonas_a_excluir)]

    if df_para_grupo.empty:
        return {"resultados_zona": pd.DataFrame(), "resultados_cobrador": pd.DataFrame()}

    # --- 1. Preparación de columnas requeridas ---
    required_cols = {
        'Meta_$': 0,
        'Recaudo_Meta': 0,  
        'Total_Recaudo_Sin_Anti': 0,
        'Meta_T.R_$': 0
    }
    for col, default in required_cols.items():
        if col not in df_para_grupo.columns:
            df_para_grupo[col] = default
        df_para_grupo[col] = pd.to_numeric(df_para_grupo[col], errors='coerce').fillna(0)
    
    # --- 2. Agregación Principal por Zona y Franja_Meta (para gráficos/tablas existentes) ---
    group_by_cols_zona = ['Zona', 'Franja_Meta']
    if 'Regional_Cobro' in df_para_grupo.columns:
        group_by_cols_zona.insert(0, 'Regional_Cobro')

    resultados_zona = df_para_grupo.groupby(group_by_cols_zona).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Recaudo_Meta', 'sum'), 
        Recaudo_Sin_Anti_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Recaudo_Meta_Total=('Meta_T.R_$', 'sum')
    ).reset_index()

    resultados_zona['Cumplimiento_%'] = 0.0
    mask_meta_valida_zona = resultados_zona['Meta_Total'] > 0
    resultados_zona.loc[mask_meta_valida_zona, 'Cumplimiento_%'] = (
        resultados_zona.loc[mask_meta_valida_zona, 'Recaudo_Total'] / resultados_zona.loc[mask_meta_valida_zona, 'Meta_Total']
    )
    
    # --- 3. NUEVA Agregación por Cobrador ---
    # Usamos las mismas métricas
    group_by_cols_cobrador = ['Cobrador', 'Franja_Meta']
    if 'Regional_Cobro' in df_para_grupo.columns:
         group_by_cols_cobrador.insert(0, 'Regional_Cobro')
    
    # Eliminamos las filas donde el cobrador es nulo o vacío
    df_cobrador = df_para_grupo[df_para_grupo['Cobrador'].notna() & (df_para_grupo['Cobrador'] != '')].copy()

    resultados_cobrador = df_cobrador.groupby(group_by_cols_cobrador).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Recaudo_Meta', 'sum'), 
        Recaudo_Sin_Anti_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Recaudo_Meta_Total=('Meta_T.R_$', 'sum')
    ).reset_index()
    
    resultados_cobrador['Cumplimiento_%'] = 0.0
    mask_meta_valida_cobrador = resultados_cobrador['Meta_Total'] > 0
    resultados_cobrador.loc[mask_meta_valida_cobrador, 'Cumplimiento_%'] = (
        resultados_cobrador.loc[mask_meta_valida_cobrador, 'Recaudo_Total'] / resultados_cobrador.loc[mask_meta_valida_cobrador, 'Meta_Total']
    )


    # Devolver un diccionario con ambos DataFrames
    return {
        "resultados_zona": resultados_zona, 
        "resultados_cobrador": resultados_cobrador # <-- NUEVO DATAFRAME
    }

@st.cache_data
def prepare_tab4_data(df_cartera, df_novedades):
    return {
        "cartera_para_mostrar": df_cartera,
        "novedades_para_mostrar": df_novedades
    }

@st.cache_data
def prepare_tab5_data(df_cartera):
    df = df_cartera.copy()
    numeric_cols = ['Total_Cuotas', 'Cuotas_Pagadas', 'Dias_Atraso_Final']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)
    df_potenciales = df[df['Dias_Atraso_Final'] <= 30].copy()
    df_potenciales = df_potenciales[df_potenciales['Total_Cuotas'] >= 6].copy()
    df_potenciales['Cuotas_Restantes'] = df_potenciales['Total_Cuotas'] - df_potenciales['Cuotas_Pagadas']
    condicion_A = (
        (df_potenciales['Total_Cuotas'].between(6, 8)) &
        (df_potenciales['Cuotas_Restantes'].between(1, 2))
    )
    condicion_B = (
        (df_potenciales['Total_Cuotas'] > 8) &
        (df_potenciales['Cuotas_Restantes'].between(1, 4))
    )
    df_final = df_potenciales[condicion_A | condicion_B]
    return {
        "potenciales_retanqueo": df_final
    }

# @st.cache_data
# def prepare_tab6_data(df_cartera_filtrada, df_novedades_filtrada, df_llamadas_filtrada, df_mensajeria_filtrada):
#     """
#     Prepara los datos para el reporte de Call Centers en el Tab 6.
#     Usa DFs que ya han sido filtrados globalmente.
#     Calcula estadísticas de llamadas.
#     """
#     if df_cartera_filtrada.empty:
#         return {
#             "reporte_raw": pd.DataFrame(),
#             "rodamiento_data": pd.DataFrame(),
#             "cartera_detallada_call_center": pd.DataFrame(),
#             "df_llamadas_filtrada": pd.DataFrame(),
#             "df_mensajeria_filtrada": pd.DataFrame(),
#             "llamadas_stats": {"total_llamadas": 0, "con_respuesta": 0, "sin_respuesta": 0},
#             "df_grafico_llamadas": pd.DataFrame(),
#             "df_efectividad_call": pd.DataFrame(),
#             "df_llamadas_por_dia": pd.DataFrame(),
#             "alerta_umbral": 0,
#             "df_funnel_mensajeria": pd.DataFrame(),
#             "df_efectividad_mensajeria": pd.DataFrame()
#         }
    
#     df = df_cartera_filtrada.copy()
#     if 'Total_Recaudo' in df.columns:
#         df['Estado_Pago'] = np.where(df['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
#     else:
#         df['Estado_Pago'] = 'SIN DATO'

#     if 'Cantidad_Novedades' in df.columns:
#         df['Estado_Gestion'] = np.where(df['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')
#     else:
#         df['Estado_Gestion'] = 'SIN DATO'

#     columnas_numericas = ['Meta_General', 'Meta_$', 'Recaudo_Meta']
#     for col in columnas_numericas:
#         if col in df.columns:
#             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
#         else:
#             df[col] = 0

#     columnas_texto = [
#         'Zona', 'Cobrador', 'Call_Center_Apoyo', 'Nombre_Call_Center', 
#         'Franja_Meta', 'Rodamiento', 'Estado_Gestion', 'Estado_Pago'
#     ]
#     for col in columnas_texto:
#         if col in df.columns:
#             df[col] = df[col].astype(str).str.strip().str.upper().replace('NAN', 'SIN DATO')
#         else:
#             df[col] = 'SIN DATO'

#     call_centers_zona = ['CL1', 'CL2', 'CL3', 'CL4']
#     call_centers_apoyo = ['CL5', 'CL6', 'CL7', 'CL8', 'CL9']
    
#     df_detalle_call_centers = df[
#         df['Zona'].isin(call_centers_zona) | df['Call_Center_Apoyo'].isin(call_centers_apoyo)
#     ].copy()

#     if not df_novedades_filtrada.empty and 'Cedula_Cliente' in df_novedades_filtrada.columns:
#         df_novedades_limpia = df_novedades_filtrada.copy()
        
#         if 'Tipo_Novedad' not in df_novedades_limpia.columns:
#             df_novedades_limpia['Tipo_Novedad'] = 'N/A'
#         if 'Novedad' not in df_novedades_limpia.columns:
#             df_novedades_limpia['Novedad'] = 'N/A'
            
#         cols_to_merge = ['Cedula_Cliente', 'Tipo_Novedad', 'Novedad']
#         df_novedades_detalle = df_novedades_limpia[cols_to_merge]
#         df_detalle_call_centers = df_detalle_call_centers.merge(
#             df_novedades_detalle, 
#             on='Cedula_Cliente', 
#             how='left'
#         )
        
#         df_detalle_call_centers['Tipo_Novedad'] = df_detalle_call_centers['Tipo_Novedad'].fillna('SIN NOVEDAD').astype(str).str.strip().str.upper()
#         df_detalle_call_centers['Novedad'] = df_detalle_call_centers['Novedad'].fillna('') 
        
#     else:
#         df_detalle_call_centers['Tipo_Novedad'] = 'SIN NOVEDAD'
#         df_detalle_call_centers['Novedad'] = ''


#     df_cl1_4 = df[(df['Zona'].isin(call_centers_zona)) & (df['Franja_Meta'] == 'AL DIA')]
#     if not df_cl1_4.empty:
#         agg_cl1_4 = df_cl1_4.groupby(['Zona', 'Cobrador']).agg(
#             Meta_General=('Meta_General', 'sum'),
#             Recaudo_Meta=('Recaudo_Meta', 'sum')
#         ).reset_index()
#         agg_cl1_4.rename(columns={'Zona': 'CALL_CENTER', 'Cobrador': 'NOMBRE', 'Meta_General': 'META_$'}, inplace=True)
#     else:
#         agg_cl1_4 = pd.DataFrame(columns=['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta'])

#     df_cl5_9 = df[df['Call_Center_Apoyo'].isin(call_centers_apoyo)]
#     if not df_cl5_9.empty:
#         agg_cl5_9 = df_cl5_9.groupby(['Call_Center_Apoyo', 'Nombre_Call_Center']).agg(
#             Meta_Dollar=('Meta_$', 'sum'),
#             Recaudo_Meta=('Recaudo_Meta', 'sum')
#         ).reset_index()
#         agg_cl5_9.rename(columns={'Call_Center_Apoyo': 'CALL_CENTER', 'Nombre_Call_Center': 'NOMBRE', 'Meta_Dollar': 'META_$'}, inplace=True)
#     else:
#         agg_cl5_9 = pd.DataFrame(columns=['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta'])

#     df_reporte = pd.concat([agg_cl1_4, agg_cl5_9], ignore_index=True)

#     reporte_raw = pd.DataFrame()
#     if not df_reporte.empty:
#         df_reporte['Faltante'] = df_reporte['META_$'] - df_reporte['Recaudo_Meta']
#         df_reporte['Cumplimiento'] = np.where(df_reporte['META_$'] > 0, df_reporte['Recaudo_Meta'] / df_reporte['META_$'], 0)
#         columnas_finales_raw = ['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta', 'Faltante', 'Cumplimiento']
#         reporte_raw = df_reporte[columnas_finales_raw].sort_values(by='CALL_CENTER').reset_index(drop=True)

#     agg_rodamiento = pd.DataFrame() 
#     if not df_detalle_call_centers.empty and 'Rodamiento' in df_detalle_call_centers.columns:
#         agg_rodamiento = df_detalle_call_centers.groupby('Rodamiento').size().reset_index(name='count')
        
#     llamadas_stats = {}
#     df_grafico_llamadas = pd.DataFrame()
    
#     if not df_llamadas_filtrada.empty and 'Estado_Llamada' in df_llamadas_filtrada.columns:
#         df_llamadas_limpio = df_llamadas_filtrada.copy()
        
#         df_llamadas_limpio['Estado_Llamada'] = df_llamadas_limpio['Estado_Llamada'].astype(str).str.strip().str.upper()
        
#         total_llamadas = len(df_llamadas_limpio)
#         con_respuesta = len(df_llamadas_limpio[df_llamadas_limpio['Estado_Llamada'] == 'ANSWERED'])
#         sin_respuesta = total_llamadas - con_respuesta
        
#         llamadas_stats = {
#             "total_llamadas": total_llamadas,
#             "con_respuesta": con_respuesta,
#             "sin_respuesta": sin_respuesta
#         }
        
#         df_grafico_llamadas = pd.DataFrame({
#             "Tipo": ["CON RESPUESTA", "SIN RESPUESTA"],
#             "Cantidad": [con_respuesta, sin_respuesta]
#         })
#         try:
#             agg_calls = df_llamadas_limpio.groupby('Call_Center_Limpio').agg(
#                 Total_Intentos=('Estado_Llamada', 'size'),
#                 Con_Respuesta=('Estado_Llamada', lambda x: (x == 'ANSWERED').sum())
#             ).reset_index()
            
#             agg_calls['Efectividad'] = np.where(
#                 agg_calls['Total_Intentos'] > 0,
#                 agg_calls['Con_Respuesta'] / agg_calls['Total_Intentos'],
#                 0
#             )
#             agg_calls.rename(columns={'Call_Center_Limpio': 'Call_Center'}, inplace=True)
#             df_efectividad_call = agg_calls.sort_values(by='Efectividad', ascending=False)
        
#         except Exception as e:
#             st.error(f"Error calculando efectividad de llamadas: {e}")
#             df_efectividad_call = pd.DataFrame()

#         if 'Call_Center_Limpio' in df_llamadas_limpio.columns:
#             n_call_centers = df_llamadas_limpio['Call_Center_Limpio'].nunique()
#             if n_call_centers > 0:
#                 alerta_umbral = n_call_centers * 30    
#         if 'Fecha_Llamada' in df_llamadas_limpio.columns:
#             try:
#                 # Convertir a datetime y normalizar a solo fecha (sin hora)
#                 df_llamadas_limpio['Fecha_Dia'] = pd.to_datetime(df_llamadas_limpio['Fecha_Llamada']).dt.date
                
#                 # --- [NUEVO] Excluir fines de semana (Sábado=5, Domingo=6) ---
#                 dias_semana = pd.to_datetime(df_llamadas_limpio['Fecha_Dia']).dt.dayofweek
#                 df_llamadas_habiles = df_llamadas_limpio[~dias_semana.isin([5, 6])].copy()
                
#                 if df_llamadas_habiles.empty:
#                     st.info("No se encontraron registros de llamadas en días hábiles para la tendencia.")
#                     df_llamadas_por_dia = pd.DataFrame()
#                 else:
#                     # Mapear estado para el filtro
#                     df_llamadas_habiles['Estado_Respuesta'] = np.where(
#                         df_llamadas_habiles['Estado_Llamada'] == 'ANSWERED',
#                         'CON RESPUESTA',
#                         'SIN RESPUESTA'
#                     )
                    
#                     # Agrupar por fecha y estado
#                     df_llamadas_dia_agg = df_llamadas_habiles.groupby(['Fecha_Dia', 'Estado_Respuesta']).size().reset_index(name='Total_Llamadas')
#                     # Renombrar 'Fecha_Dia' para que el gráfico la reconozca
#                     df_llamadas_dia_agg.rename(columns={'Fecha_Dia': 'Fecha'}, inplace=True)
                    
#                     # Asignar al DataFrame principal
#                     df_llamadas_por_dia = df_llamadas_dia_agg
                
#             except Exception as e:
#                 st.warning(f"Error procesando fechas para gráfico de llamadas por día: {e}")
#                 df_llamadas_por_dia = pd.DataFrame() # Asegurarse que sea un DF vacío en caso de error
#         else:
#             st.warning("No se encontró la columna 'Fecha_Llamada' para el gráfico de tendencia.")
#             df_llamadas_por_dia = pd.DataFrame() # Asegurarse que sea un DF vacío
#     else:
#         llamadas_stats = {
#             "total_llamadas": 0,
#             "con_respuesta": 0,
#             "sin_respuesta": 0
#         }
#         df_grafico_llamadas = pd.DataFrame({
#             "Tipo": ["CON RESPUESTA", "SIN RESPUESTA"],
#             "Cantidad": [0, 0]
#         })
#         df_efectividad_call = pd.DataFrame()
#         df_llamadas_por_dia = pd.DataFrame()
#         alerta_umbral=0
        
#     df_funnel_mensajeria = pd.DataFrame()
#     df_efectividad_mensajeria = pd.DataFrame()
    
#     # Necesitamos los 3 DFs: mensajeria, novedades, y cartera (df)
#     if not df_mensajeria_filtrada.empty and not df_novedades_filtrada.empty and not df.empty:
#         try:
#             # --- Paso 1: Mensajes Entregados ---
#             df_mensajeria_limpio = df_mensajeria_filtrada.copy()
#             total_mensajes = len(df_mensajeria_limpio)
            
#             # --- Paso 2: Conversaciones ---
#             if 'Primer_Mensaje_Agente' in df_mensajeria_limpio.columns:
#                 df_mensajeria_limpio['Primer_Mensaje_Agente'] = df_mensajeria_limpio['Primer_Mensaje_Agente'].astype(str).replace('nan', '')
#                 df_mensajeria_limpio['Es_Conversacion'] = np.where(
#                     df_mensajeria_limpio['Primer_Mensaje_Agente'].notna() &
#                     (df_mensajeria_limpio['Primer_Mensaje_Agente'] != '') &
#                     (df_mensajeria_limpio['Primer_Mensaje_Agente'] != 'None'),
#                     1,
#                     0
#                 )
                
#                 df_conversaciones = df_mensajeria_limpio[df_mensajeria_limpio['Es_Conversacion'] == 1].copy()
#                 total_conversaciones = len(df_conversaciones)
#             else:
#                 st.warning("Columna 'Primer_Mensaje_Agente' no encontrada en datos de mensajería.")
#                 total_conversaciones = 0
#                 df_conversaciones = pd.DataFrame()
                
#             if 'Call_Center' in df_mensajeria_limpio.columns:
#                 agg_msgs = df_mensajeria_limpio.groupby('Call_Center').agg(
#                     Total_Entregados=('Primer_Mensaje_Agente', 'size'),
#                     Total_Conversaciones=('Es_Conversacion', 'sum')
#                 ).reset_index()
                
#                 agg_msgs['Efectividad'] = np.where(
#                     agg_msgs['Total_Entregados'] > 0,
#                     agg_msgs['Total_Conversaciones'] / agg_msgs['Total_Entregados'],
#                     0
#                 )
#                 df_efectividad_mensajeria = agg_msgs.sort_values(by='Efectividad', ascending=False)
#             else:
#                 st.warning("Columna 'Call_Center' no encontrada en datos de mensajería para gráfico de efectividad.")
#                 df_efectividad_mensajeria = pd.DataFrame() 

#             # --- Paso 3: Gestion en Sistema ---
#             if not df_conversaciones.empty and 'Numero_Telefono' in df_conversaciones.columns:
                
#                 # --- [CORREGIDO] Normalizar teléfonos de Novedades ---
#                 telefonos_novedades = set()
#                 if 'Telefono_Cliente' in df_novedades_filtrada.columns:
#                     # Convertir a str, quitar nulos, y quitar ".0" del final
#                     telefonos_novedades.update(
#                         df_novedades_filtrada['Telefono_Cliente'].dropna().astype(str).str.replace(r'\.0$', '', regex=True)
#                     )
#                 if 'Celular_Cliente' in df_novedades_filtrada.columns:
#                     # Convertir a str, quitar nulos, y quitar ".0" del final
#                     telefonos_novedades.update(
#                         df_novedades_filtrada['Celular_Cliente'].dropna().astype(str).str.replace(r'\.0$', '', regex=True)
#                     )
                
#                 if not telefonos_novedades:
#                     st.warning("No se encontraron teléfonos en 'Detalle_Novedades' para cruzar.")
#                     total_gestion_sistema = 0
#                     df_gestion_sistema = pd.DataFrame()
#                 else:
#                     # --- [CORREGIDO] Normalizar Numero_Telefono de Conversaciones ---
#                     df_conversaciones['Numero_Telefono_Norm'] = df_conversaciones['Numero_Telefono'].astype(str).str.replace(r'\.0$', '', regex=True)
                    
#                     # Comparar los números normalizados
#                     df_gestion_sistema = df_conversaciones[
#                         df_conversaciones['Numero_Telefono_Norm'].isin(telefonos_novedades)
#                     ].copy()
#                     total_gestion_sistema = len(df_gestion_sistema)
#             else:
#                 total_gestion_sistema = 0
#                 df_gestion_sistema = pd.DataFrame()

#             # --- Paso 4: Clientes con Pago ---
#             if not df_gestion_sistema.empty:
#                 # 4a. Obtener Cédulas de clientes que PAGARON (de 'Analisis_de_Cartera' -> df)
#                 if 'Cedula_Cliente' in df.columns and 'Estado_Pago' in df.columns:
#                     cedulas_con_pago = set(df[df['Estado_Pago'] == 'PAGO']['Cedula_Cliente'].dropna().astype(str))
#                 else:
#                     cedulas_con_pago = set()
                
#                 if not cedulas_con_pago:
#                     total_clientes_pago = 0
#                 else:
#                     # 4b. Crear mapa de Telefono -> Cedula desde df_novedades_filtrada
#                     # --- [CORREGIDO] Usar teléfonos normalizados para el mapeo ---
#                     map_tel_a_cedula = {}
#                     df_novedades_map = df_novedades_filtrada.dropna(subset=['Cedula_Cliente']).copy() # Usar .copy()
                    
#                     if 'Telefono_Cliente' in df_novedades_map.columns:
#                         # Crear columna normalizada ANTES de usarla como índice
#                         df_novedades_map['Telefono_Cliente_Norm'] = df_novedades_map['Telefono_Cliente'].astype(str).str.replace(r'\.0$', '', regex=True)
#                         map1 = df_novedades_map.set_index('Telefono_Cliente_Norm')['Cedula_Cliente'].astype(str).to_dict()
#                         map_tel_a_cedula.update(map1)
                        
#                     if 'Celular_Cliente' in df_novedades_map.columns:
#                         # Crear columna normalizada ANTES de usarla como índice
#                         df_novedades_map['Celular_Cliente_Norm'] = df_novedades_map['Celular_Cliente'].astype(str).str.replace(r'\.0$', '', regex=True)
#                         map2 = df_novedades_map.set_index('Celular_Cliente_Norm')['Cedula_Cliente'].astype(str).to_dict()
#                         map_tel_a_cedula.update(map2)
                    
#                     if not map_tel_a_cedula:
#                         total_clientes_pago = 0
#                     else:
#                         # 4c. Mapear y Contar
#                         # Re-usamos la columna 'Numero_Telefono_Norm' que ya creamos en el Paso 3
#                         df_gestion_sistema['Cedula_Mapeada'] = df_gestion_sistema['Numero_Telefono_Norm'].map(map_tel_a_cedula)
#                         total_clientes_pago = df_gestion_sistema['Cedula_Mapeada'].isin(cedulas_con_pago).sum()
#             else:
#                 total_clientes_pago = 0
#             data_funnel = {
#                 'Etapa': ['Mensajes Entregados', 'Conversaciones', 'Gestion en Sistema', 'Clientes con Pago'],
#                 'Cantidad': [total_mensajes, total_conversaciones, total_gestion_sistema, total_clientes_pago]
#             }
#             df_funnel_mensajeria = pd.DataFrame(data_funnel)

#         except Exception as e:
#             st.error(f"Error al procesar el embudo de mensajería: {e}")
#             df_funnel_mensajeria = pd.DataFrame()
#     else:
#         df_funnel_mensajeria = pd.DataFrame()
#         df_efectividad_mensajeria = pd.DataFrame()  
#     return {
#         "reporte_raw": reporte_raw,
#         "rodamiento_data": agg_rodamiento,
#         "cartera_detallada_call_center": df_detalle_call_centers,
#         "df_llamadas_filtrada": df_llamadas_filtrada,       
#         "df_mensajeria_filtrada": df_mensajeria_filtrada, 
#         "llamadas_stats": llamadas_stats,                  
#         "df_grafico_llamadas": df_grafico_llamadas,
#         "df_efectividad_call": df_efectividad_call, 
#         "df_llamadas_por_dia": df_llamadas_por_dia,
#         "alerta_umbral": alerta_umbral,
#         "df_funnel_mensajeria": df_funnel_mensajeria,
#         "df_efectividad_mensajeria": df_efectividad_mensajeria
#     }