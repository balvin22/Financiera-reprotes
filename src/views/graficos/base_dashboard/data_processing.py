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
        return {} # Retornamos un diccionario vacio si no hay datos para mostrar

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

    df_cartera = df_cartera.copy()

    df_cartera['Estado_Pago'] = np.where(df_cartera['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
    cargos_unicos_por_cliente = df_novedades[['Cedula_Cliente', 'Cargo_Usuario']].drop_duplicates()
    agg_donut = df_cartera['Estado_Pago'].value_counts()

    # --- 2. Datos para los Sunburst Charts (sin cambios) ---
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

        # 4.3. Rellenamos los valores nulos con 0 y convertimos a entero.
        df_para_tabla['Novedades_Por_Cargo'] = df_para_tabla['Novedades_Por_Cargo'].fillna(0).astype(int)
    else:
        # Si no hay novedades, creamos la columna con ceros para evitar errores.
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
