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
    if not df_novedades.empty:
        novedades_por_cargo_cliente = df_novedades.groupby(['Cedula_Cliente', 'Cargo_Usuario']).size().reset_index(name='Novedades_Por_Cargo')
        df_para_tabla = pd.merge(
            df_merged,
            novedades_por_cargo_cliente,
            on=['Cedula_Cliente', 'Cargo_Usuario'],
            how='left'
        )
        df_para_tabla['Novedades_Por_Cargo'] = df_para_tabla['Novedades_Por_Cargo'].fillna(0).astype(int)
    else:
        df_para_tabla = df_merged.copy()
        df_para_tabla['Novedades_Por_Cargo'] = 0

    return {
        "donut_data": agg_donut,
        "sunburst_initial_grouped": grouped_sunburst_inicial,
        "sunburst_initial_counts": conteo_gestion_inicial,
        "rodamiento_data": agg_rodamiento,
        "detalle_pago": (grouped_detalle_pago, conteo_detalle_pago),
        "detalle_sin_pago": (grouped_detalle_sin_pago, conteo_detalle_sin_pago),
        "processed_cartera": df_cartera,
        "processed_data_merged": df_merged, 
        "data_para_tabla": df_para_tabla
    }

@st.cache_data
def prepare_tab3_data(df):
    """
    Toma el dataframe filtrado globalmente y realiza la agregación principal
    por Zona y Franja_Meta para el Tab de Resultados.
    Esta función es el único punto de procesamiento de datos para el Tab 3.
    """
    franjas_a_usar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
    df_para_grupo = df[df['Franja_Meta'].isin(franjas_a_usar)]

    if df_para_grupo.empty:
        return pd.DataFrame()

    # Columnas necesarias para los cálculos
    required_cols = {
        'Meta_$': 0,
        'Total_Recaudo': 0,
        'Total_Recaudo_Sin_Anti': 0,
        'Meta_T.R_$': 0
    }
    for col, default in required_cols.items():
        if col not in df_para_grupo.columns:
            df_para_grupo[col] = default
        # Asegurar que la columna sea numérica
        df_para_grupo[col] = pd.to_numeric(df_para_grupo[col], errors='coerce').fillna(0)
    
    group_by_cols = ['Zona', 'Franja_Meta']
    if 'Regional_Cobro' in df_para_grupo.columns:
        group_by_cols.insert(0, 'Regional_Cobro')

    resultados = df_para_grupo.groupby(group_by_cols).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Total_Recaudo', 'sum'),
        Recaudo_Sin_Anti_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Recaudo_Meta_Total=('Meta_T.R_$', 'sum')
    ).reset_index()

    # Cálculo de cumplimiento, manejando división por cero de forma segura
    resultados['Cumplimiento_%'] = 0.0
    mask_meta_valida = resultados['Meta_Total'] > 0
    resultados.loc[mask_meta_valida, 'Cumplimiento_%'] = (
        resultados.loc[mask_meta_valida, 'Recaudo_Total'] / resultados.loc[mask_meta_valida, 'Meta_Total']
    )
    return resultados

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
    
def prepare_tab6_data(df_cartera, df_novedades):
    """
    Prepara los datos para el reporte de Call Centers en el Tab 6.
    Filtra los créditos que pertenecen a Call Centers para la tabla de detalle
    y luego une las novedades.
    """
    if df_cartera.empty:
        return {}
    
    df = df_cartera.copy()

    # --- NUEVO: Se añaden los cálculos para Estado_Pago y Estado_Gestion ---
    # Se calcula 'Estado_Pago' basado en el recaudo.
    if 'Total_Recaudo' in df.columns:
        df['Estado_Pago'] = np.where(df['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
    else:
        df['Estado_Pago'] = 'SIN DATO'

    # Se calcula 'Estado_Gestion' basado en la cantidad de novedades.
    if 'Cantidad_Novedades' in df.columns:
        df['Estado_Gestion'] = np.where(df['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')
    else:
        df['Estado_Gestion'] = 'SIN DATO'
    
    # --- Limpieza de Datos (Se realiza después de crear las columnas) ---
    columnas_numericas = ['Meta_General', 'Meta_$', 'Recaudo_Meta']
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    columnas_texto = [
        'Zona', 'Cobrador', 'Call_Center_Apoyo', 'Nombre_Call_Center', 
        'Franja_Meta', 'Rodamiento', 'Estado_Gestion', 'Estado_Pago'
    ]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().replace('NAN', 'SIN DATO')
        else:
            df[col] = 'SIN DATO'

    # --- Filtrar créditos que pertenecen a Call Centers ---
    call_centers_zona = ['CL1', 'CL2', 'CL3', 'CL4']
    call_centers_apoyo = ['CL5', 'CL6', 'CL7', 'CL8', 'CL9']
    
    df_detalle_call_centers = df[
        df['Zona'].isin(call_centers_zona) | df['Call_Center_Apoyo'].isin(call_centers_apoyo)
    ].copy()

    # --- Procesamiento de Novedades y Unión ---
    if not df_novedades.empty and 'Cedula_Cliente' in df_novedades.columns:
        df_novedades_limpia = df_novedades.copy()
        if 'Fecha_Novedad' in df_novedades_limpia.columns:
            df_novedades_limpia = df_novedades_limpia.sort_values('Fecha_Novedad', ascending=False)
        
        df_last_novedad = df_novedades_limpia.drop_duplicates(subset=['Cedula_Cliente'], keep='first')[['Cedula_Cliente', 'Tipo_Novedad']]
        
        df_detalle_call_centers = df_detalle_call_centers.merge(df_last_novedad, on='Cedula_Cliente', how='left')
        df_detalle_call_centers['Tipo_Novedad'] = df_detalle_call_centers['Tipo_Novedad'].fillna('SIN NOVEDAD').astype(str).str.strip().str.upper()
    else:
        df_detalle_call_centers['Tipo_Novedad'] = 'SIN NOVEDAD'

    # --- Procesar Metas de Call Centers ---
    df_cl1_4 = df[(df['Zona'].isin(call_centers_zona)) & (df['Franja_Meta'] == 'AL DIA')]
    if not df_cl1_4.empty:
        agg_cl1_4 = df_cl1_4.groupby(['Zona', 'Cobrador']).agg(
            Meta_General=('Meta_General', 'sum'),
            Recaudo_Meta=('Recaudo_Meta', 'sum')
        ).reset_index()
        agg_cl1_4.rename(columns={'Zona': 'CALL_CENTER', 'Cobrador': 'NOMBRE', 'Meta_General': 'META_$'}, inplace=True)
    else:
        agg_cl1_4 = pd.DataFrame(columns=['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta'])

    df_cl5_9 = df[df['Call_Center_Apoyo'].isin(call_centers_apoyo)]
    if not df_cl5_9.empty:
        agg_cl5_9 = df_cl5_9.groupby(['Call_Center_Apoyo', 'Nombre_Call_Center']).agg(
            Meta_Dollar=('Meta_$', 'sum'),
            Recaudo_Meta=('Recaudo_Meta', 'sum')
        ).reset_index()
        agg_cl5_9.rename(columns={'Call_Center_Apoyo': 'CALL_CENTER', 'Nombre_Call_Center': 'NOMBRE', 'Meta_Dollar': 'META_$'}, inplace=True)
    else:
        agg_cl5_9 = pd.DataFrame(columns=['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta'])

    df_reporte = pd.concat([agg_cl1_4, agg_cl5_9], ignore_index=True)

    # --- Formatear Reporte de Metas ---
    reporte_raw = pd.DataFrame()
    if not df_reporte.empty:
        df_reporte['Faltante'] = df_reporte['META_$'] - df_reporte['Recaudo_Meta']
        df_reporte['Cumplimiento'] = np.where(df_reporte['META_$'] > 0, df_reporte['Recaudo_Meta'] / df_reporte['META_$'], 0)
        columnas_finales_raw = ['CALL_CENTER', 'NOMBRE', 'META_$', 'Recaudo_Meta', 'Faltante', 'Cumplimiento']
        reporte_raw = df_reporte[columnas_finales_raw].sort_values(by='CALL_CENTER').reset_index(drop=True)

    # --- Preparar datos para el gráfico de rodamientos ---
    agg_rodamiento = pd.DataFrame() 
    if not df_detalle_call_centers.empty and 'Rodamiento' in df_detalle_call_centers.columns:
        agg_rodamiento = df_detalle_call_centers.groupby('Rodamiento').size().reset_index(name='count')
        
    return {
        "reporte_raw": reporte_raw,
        "rodamiento_data": agg_rodamiento,
        "cartera_detallada_call_center": df_detalle_call_centers
    }