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
        return {} # Devuelve un diccionario vacío si no hay datos

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
        # 1. Copiamos la columna original para no modificarla.
        df_vigencia_copy = df[['Fecha_Cuota_Vigente']].copy()
        
        # 2. Convertimos a fecha, los textos como 'ANTICIPADO' se volverán NaT (Not a Time).
        fechas_reales = pd.to_datetime(df_vigencia_copy['Fecha_Cuota_Vigente'], errors='coerce')
        
        # 3. Creamos la nueva columna 'Estado_Vigencia_Agrupado'
        # Por defecto, todo lo que sea una fecha válida se marcará como 'VIGENTES'.
        df_vigencia_copy['Estado_Vigencia_Agrupado'] = 'VIGENTES'
        
        # 4. Corregimos las etiquetas: Donde no hay una fecha válida (es NaT),
        # usamos el valor original de la columna (que sería 'ANTICIPADO', 'VIGENCIA EXPIRADA', etc.).
        df_vigencia_copy.loc[fechas_reales.isna(), 'Estado_Vigencia_Agrupado'] = df_vigencia_copy['Fecha_Cuota_Vigente']

        # 5. El resto de tu lógica para sub-estados funciona sobre las fechas ya identificadas.
        df_vigencia_copy['Sub_Estado_Vigencia'] = ''
        
        # Máscara para encontrar solo las filas que son 'VIGENTES'
        vigentes_mask = df_vigencia_copy['Estado_Vigencia_Agrupado'] == 'VIGENTES'
        
        if vigentes_mask.any():
            # Filtramos las fechas que corresponden a 'VIGENTES'
            fechas_vigentes = fechas_reales[vigentes_mask]
            
            current_year, current_month = datetime.now().year, datetime.now().month
            
            # Filtramos las fechas vigentes que son del mes y año actual
            fechas_mes_actual = fechas_vigentes[(fechas_vigentes.dt.year == current_year) & (fechas_vigentes.dt.month == current_month)]

            if not fechas_mes_actual.empty:
                # Creamos las etiquetas de día solo para las fechas del mes actual
                subdivision_labels = fechas_mes_actual.dt.day.apply(lambda d: f"Día {d}")
                df_vigencia_copy.loc[fechas_mes_actual.index, 'Sub_Estado_Vigencia'] = subdivision_labels
        
        # 6. Agrupamos para el gráfico. Esto ahora incluirá 'ANTICIPADO' y 'VIGENCIA EXPIRADA' correctamente.
        agg_vigencia = df_vigencia_copy.groupby(['Estado_Vigencia_Agrupado', 'Sub_Estado_Vigencia']).size().reset_index(name='count')


    # --- Devuelve un diccionario con todos los dataframes agregados ---
    return {
        "regional": agg_regional,
        "cobro": agg_cobro,
        "desembolso": agg_desembolso,
        "vigencia": agg_vigencia,
    }
    
@st.cache_data
def prepare_tab2_data(df_cartera, df_novedades):
    """
    Prepara y cachea todos los datos necesarios para los gráficos del Tab 2.
    """
    if df_cartera.empty:
        return {}

    df_cartera = df_cartera.copy()

    # --- 1. Datos para el Donut Chart (prepare_donut_data) ---
    df_cartera['Estado_Pago'] = np.where(df_cartera['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
    agg_donut = df_cartera['Estado_Pago'].value_counts()

    # --- 2. Datos para los Sunburst Charts (prepare_sunburst_data) ---
    # Esta es la parte más costosa: el merge. Lo hacemos UNA SOLA VEZ.
    df_cartera['Estado_Gestion'] = np.where(df_cartera['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')
    # Obtenemos una tabla con las combinaciones únicas de Cédula y Cargo.
    cargos_unicos_por_cliente = df_novedades[['Cedula_Cliente', 'Cargo_Usuario']].drop_duplicates()
    # <--- CAMBIO CLAVE 2: Hacemos el merge. Pandas automáticamente creará las filas duplicadas necesarias.
    df_merged = pd.merge(df_cartera, cargos_unicos_por_cliente, on='Cedula_Cliente', how='left')
    # Rellenamos los NaN para créditos que no tuvieron ninguna gestión.
    df_merged['Cargo_Usuario'] = df_merged['Cargo_Usuario'].fillna('')
    
    # Pre-cálculo para el primer sunburst
    grouped_sunburst_inicial = df_merged.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped_sunburst_inicial = grouped_sunburst_inicial[~((grouped_sunburst_inicial['Estado_Gestion'] == 'CON GESTIÓN') & (grouped_sunburst_inicial['Cargo_Usuario'] == ''))]
    conteo_gestion_inicial = df_merged['Estado_Gestion'].value_counts()

    # --- 3. Datos para el Gráfico de Rodamiento ---
    agg_rodamiento = None
    if 'Rodamiento' in df_cartera.columns and 'Estado_Gestion' in df_cartera.columns:
        # <-- CAMBIO: Agrupamos por 'Rodamiento' y 'Estado_Gestion'
        agg_rodamiento = df_cartera.groupby(['Rodamiento', 'Estado_Gestion']).size().reset_index(name='Número de Cuentas')
        # <-- CAMBIO: La lógica de ordenar por franjas ya no es necesaria y se elimina
        
    df_pago = df_merged[df_merged['Estado_Pago'] == 'PAGO']
    df_sin_pago = df_merged[df_merged['Estado_Pago'] == 'SIN PAGO']

    # Agrupamos los subconjuntos UNA SOLA VEZ
    grouped_detalle_pago = df_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    conteo_detalle_pago = df_pago['Estado_Gestion'].value_counts()
    
    grouped_detalle_sin_pago = df_sin_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    conteo_detalle_sin_pago = df_sin_pago['Estado_Gestion'].value_counts()

    return {
        "donut_data": agg_donut,
        "sunburst_initial_grouped": grouped_sunburst_inicial,
        "sunburst_initial_counts": conteo_gestion_inicial,
        "rodamiento_data": agg_rodamiento,
        # Devolvemos los nuevos resultados pre-calculados
        "detalle_pago": (grouped_detalle_pago, conteo_detalle_pago),
        "detalle_sin_pago": (grouped_detalle_sin_pago, conteo_detalle_sin_pago),
        "processed_cartera": df_cartera,
        "processed_data_merged": df_merged
    }