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

    # --- 4. Datos para: create_vigencia_sunburst_chart (OPTIMIZADO PARA TEXTOS) ---
    agg_vigencia = None
    if 'Fecha_Cuota_Vigente' in df.columns:
        df_vigencia_copy = df[['Fecha_Cuota_Vigente']].copy()
        
        # Intentamos extraer las fechas reales (lo que sea texto como "ANTICIPADO" será NaT)
        fechas_reales = pd.to_datetime(df_vigencia_copy['Fecha_Cuota_Vigente'], errors='coerce')
        
        df_vigencia_copy['Estado_Vigencia_Agrupado'] = 'VIGENTES'
        
        # Donde no hay fecha, colocamos el texto original ("VIGENCIA EXPIRADA", "ANTICIPADO")
        mask_not_date = fechas_reales.isna()
        df_vigencia_copy.loc[mask_not_date, 'Estado_Vigencia_Agrupado'] = df_vigencia_copy.loc[mask_not_date, 'Fecha_Cuota_Vigente']
        
        # Limpiamos la basura que deja la conversión a texto puro en Parquet
        df_vigencia_copy['Estado_Vigencia_Agrupado'] = df_vigencia_copy['Estado_Vigencia_Agrupado'].replace(
            {'': 'SIN ESTADO', 'nan': 'SIN ESTADO', 'NaN': 'SIN ESTADO', 'None': 'SIN ESTADO'}
        )

        df_vigencia_copy['Sub_Estado_Vigencia'] = ''
        vigentes_mask = df_vigencia_copy['Estado_Vigencia_Agrupado'] == 'VIGENTES'
    
        if vigentes_mask.any():
            fechas_vigentes = fechas_reales[vigentes_mask]
            # Extraemos el día para los vigentes
            subdivision_labels = fechas_vigentes.dt.day.apply(lambda d: f"Día {int(d)}" if pd.notna(d) else "")
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
    Prepara datos para el Tab 2 con optimización de merge.
    """
    if df_cartera.empty:
        return {}
    
    # Filtro inicial para evitar datos ruidosos
    df_cartera = df_cartera[df_cartera['Valor_Cuota_Vigente'] != 'ANTICIPADO'].copy()
    if df_cartera.empty:
        return {}

    # Lógica de estados base
    df_cartera['Estado_Pago'] = np.where(df_cartera['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
    df_cartera['Estado_Gestion'] = np.where(df_cartera['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')

    # Datos para Donut
    agg_donut = df_cartera['Estado_Pago'].value_counts()

    # Merge para Sunburst inicial (Gestión vs Cargos)
    cargos_unicos_por_cliente = df_novedades[['Cedula_Cliente', 'Cargo_Usuario']].drop_duplicates() if not df_novedades.empty else pd.DataFrame(columns=['Cedula_Cliente', 'Cargo_Usuario'])
    df_merged = pd.merge(df_cartera, cargos_unicos_por_cliente, on='Cedula_Cliente', how='left')
    df_merged['Cargo_Usuario'] = df_merged['Cargo_Usuario'].fillna('SIN CARGO')

    grouped_sunburst_inicial = df_merged.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped_sunburst_inicial = grouped_sunburst_inicial[~((grouped_sunburst_inicial['Estado_Gestion'] == 'CON GESTIÓN') & (grouped_sunburst_inicial['Cargo_Usuario'] == ''))]
    
    conteo_gestion_inicial = df_merged['Estado_Gestion'].value_counts()

    # Datos Rodamiento
    agg_rodamiento = None
    if 'Rodamiento' in df_cartera.columns:
        agg_rodamiento = df_cartera.groupby(['Rodamiento', 'Estado_Gestion']).size().reset_index(name='Número de Cuentas')

    # Detalle de Pagos
    df_pago = df_merged[df_merged['Estado_Pago'] == 'PAGO']
    df_sin_pago = df_merged[df_merged['Estado_Pago'] == 'SIN PAGO']

    grouped_detalle_pago = df_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped_detalle_sin_pago = df_sin_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')

    # Lógica de Tabla Detallada (Optimización de Memoria)
    if not df_novedades.empty:
        novedades_por_cargo = df_novedades.groupby(['Cedula_Cliente', 'Cargo_Usuario']).size().reset_index(name='Novedades_Por_Cargo')
        
        columnas_clave = [
            'Cedula_Cliente', 'Empresa', 'Credito', 'Nombre_Cliente', 'Celular', 'Nombre_Ciudad', 'Zona',
            'Dias_Atraso_Final', 'Total_Recaudo', 'Valor_Vencido', 'Codeudor1', 'Nombre_Codeudor1', 
            'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2','Telefono_Codeudor2', 'Meta_$',
            'Estado_Pago', 'Estado_Gestion', 'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente'
        ]
        cols_finales_c = [c for c in columnas_clave if c in df_cartera.columns]
        
        df_base_reducida = pd.merge(df_cartera[cols_finales_c], novedades_por_cargo, on='Cedula_Cliente', how='left')
        
        df_para_tabla = pd.merge(
            df_base_reducida, 
            df_novedades[['Cedula_Cliente', 'Cargo_Usuario', 'Novedad', 'Tipo_Novedad', 'Nombre_Usuario']], 
            on=['Cedula_Cliente', 'Cargo_Usuario'], 
            how='left'
        )
        for col in ['Novedad', 'Tipo_Novedad', 'Nombre_Usuario']:
            if col in df_para_tabla.columns:
                df_para_tabla[col] = df_para_tabla[col].fillna('')
    else:
        df_para_tabla = df_merged.copy()
        df_para_tabla['Novedades_Por_Cargo'] = 0
        df_para_tabla['Novedad'] = ''
        df_para_tabla['Tipo_Novedad'] = ''
        df_para_tabla['Nombre_Usuario'] = ''

    return {
        "donut_data": agg_donut,
        "sunburst_initial_grouped": grouped_sunburst_inicial,
        "sunburst_initial_counts": conteo_gestion_inicial,
        "rodamiento_data": agg_rodamiento,
        "detalle_pago": (grouped_detalle_pago, df_pago['Estado_Gestion'].value_counts()),
        "detalle_sin_pago": (grouped_detalle_sin_pago, df_sin_pago['Estado_Gestion'].value_counts()),
        "processed_cartera": df_cartera,
        "processed_data_merged": df_merged, 
        "data_para_tabla": df_para_tabla 
    }

@st.cache_data
def prepare_tab3_data(df):
    """      
    Agregación principal por Zona y Cobrador para Resultados.
    """
    franjas_a_usar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']    
    df_para_grupo = df[df['Franja_Meta'].isin(franjas_a_usar)].copy()
    df_para_grupo = df_para_grupo[~df_para_grupo['Zona'].isin(['CL1', 'CL2', 'CL3', 'CL4'])]

    if df_para_grupo.empty:
        return {"resultados_zona": pd.DataFrame(), "resultados_cobrador": pd.DataFrame()}

    # Tipado numérico
    required_cols = {'Meta_$': 0, 'Recaudo_Meta': 0, 'Total_Recaudo_Sin_Anti': 0, 'Meta_T.R_$': 0}
    for col, default in required_cols.items():
        if col in df_para_grupo.columns:
            df_para_grupo[col] = pd.to_numeric(df_para_grupo[col], errors='coerce').fillna(0)

    # Agregación por Zona
    gb_zona = ['Regional_Cobro', 'Zona', 'Franja_Meta'] if 'Regional_Cobro' in df_para_grupo.columns else ['Zona', 'Franja_Meta']
    resultados_zona = df_para_grupo.groupby(gb_zona).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Recaudo_Meta', 'sum'), 
        Recaudo_Sin_Anti_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Recaudo_Meta_Total=('Meta_T.R_$', 'sum'),
        Cant_Cuentas=('Zona', 'size')
    ).reset_index()

    resultados_zona['Cumplimiento_%'] = np.where(resultados_zona['Meta_Total'] > 0, resultados_zona['Recaudo_Total'] / resultados_zona['Meta_Total'], 0.0)

    # Agregación por Cobrador
    df_cobrador = df_para_grupo[df_para_grupo['Cobrador'].notna() & (df_para_grupo['Cobrador'] != '')].copy()
    gb_cobrador = ['Regional_Cobro', 'Zona', 'Cobrador'] if 'Regional_Cobro' in df_para_grupo.columns else ['Zona', 'Cobrador']
    
    resultados_cobrador = df_cobrador.groupby(gb_cobrador).agg(
        Meta_Total=('Meta_T.R_$', 'sum'),              
        Recaudo_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Cant_Cuentas=('Cobrador', 'size')
    ).reset_index()
    
    resultados_cobrador['Cumplimiento_%'] = np.where(resultados_cobrador['Meta_Total'] > 0, resultados_cobrador['Recaudo_Total'] / resultados_cobrador['Meta_Total'], 0.0)

    return {"resultados_zona": resultados_zona, "resultados_cobrador": resultados_cobrador}

@st.cache_data
def prepare_tab4_data(df_cartera, df_novedades):
    return {"cartera_para_mostrar": df_cartera, "novedades_para_mostrar": df_novedades}

@st.cache_data
def prepare_tab5_data(df_cartera):
    df = df_cartera.copy()
    numeric_cols = ['Total_Cuotas', 'Cuotas_Pagadas', 'Dias_Atraso_Final']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df.dropna(subset=numeric_cols, inplace=True)
    df_potenciales = df[(df['Dias_Atraso_Final'] <= 30) & (df['Total_Cuotas'] >= 6)].copy()
    df_potenciales['Cuotas_Restantes'] = df_potenciales['Total_Cuotas'] - df_potenciales['Cuotas_Pagadas']
    
    cond_A = (df_potenciales['Total_Cuotas'].between(6, 8)) & (df_potenciales['Cuotas_Restantes'].between(1, 2))
    cond_B = (df_potenciales['Total_Cuotas'] > 8) & (df_potenciales['Cuotas_Restantes'].between(1, 4))
    
    return {"potenciales_retanqueo": df_potenciales[cond_A | cond_B]}