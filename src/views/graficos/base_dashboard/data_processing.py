import pandas as pd
import numpy as np
from datetime import datetime
from config import ORDEN_FRANJAS, ZONA_COBRO_MAP

def prepare_tab1_data(df):
    """
    Realiza las agregaciones para los gráficos del Tab 1 de forma directa.
    Sin caché para evitar fugas de memoria con filtros dinámicos.
    """
    if df.empty:
        return {}

    # --- 1. Datos para: create_regional_bar_chart ---
    agg_regional = df.groupby(['Regional_Venta', 'Franja_Meta'], observed=True).size().reset_index(name='count')
    
    # --- 2. Datos para: create_cobro_bar_chart ---
    agg_cobro = None
    if 'Regional_Cobro' in df.columns and 'Zona_Cobro' in df.columns:
        df_cobro = df[['Regional_Cobro', 'Zona_Cobro', 'Franja_Meta']].dropna(subset=['Zona_Cobro'])
        
        mapped_zonas = df_cobro['Zona_Cobro'].map(ZONA_COBRO_MAP)
        eje_x_cobro = df_cobro['Regional_Cobro'].replace(['nan', 'NaN', ''], np.nan).fillna(mapped_zonas)
        
        df_temp = pd.DataFrame({'Eje_X_Cobro': eje_x_cobro, 'Franja_Meta': df_cobro['Franja_Meta']}).dropna(subset=['Eje_X_Cobro'])
        
        if not df_temp.empty:
            agg_cobro = df_temp.groupby(['Eje_X_Cobro', 'Franja_Meta'], observed=True).size().reset_index(name='count')

    # --- 3. Datos para: create_desembolso_por_ano_chart ---
    agg_desembolso = None
    if 'Fecha_Desembolso' in df.columns and 'Valor_Desembolso' in df.columns:
        df_desembolso = df.dropna(subset=['Fecha_Desembolso'])
        
        if not df_desembolso.empty:
            años = pd.to_datetime(df_desembolso['Fecha_Desembolso']).dt.year
            
            # Blindaje extra: asegurar que el valor sea puramente numérico
            valores_desembolso = pd.to_numeric(df_desembolso['Valor_Desembolso'], errors='coerce').fillna(0)
            
            df_temp_des = pd.DataFrame({
                'Año_Desembolso': años, 
                'Franja_Meta': df_desembolso['Franja_Meta'], 
                'Valor_Desembolso': valores_desembolso
            })
            
            start_year, end_year = 2018, datetime.now().year
            df_temp_des = df_temp_des[df_temp_des['Año_Desembolso'].between(start_year, end_year)]
            
            agg_desembolso = df_temp_des.groupby(['Año_Desembolso', 'Franja_Meta'], observed=True)['Valor_Desembolso'].sum().reset_index()
            
            # --- ¡EL FIX DEFINITIVO DESDE EL BACKEND! ---
            # Convertimos el año numérico a texto y le sumamos un espacio. 
            # Así, Plotly jamás podrá tratarlo como una fecha continua.
            if not agg_desembolso.empty:
                agg_desembolso['Año_Desembolso'] = agg_desembolso['Año_Desembolso'].astype(int).astype(str) + " "

    # --- 4. Datos para: create_vigencia_sunburst_chart ---
    agg_vigencia = None
    if 'Fecha_Cuota_Vigente' in df.columns:
        df_vigencia = df[['Fecha_Cuota_Vigente']].copy()
        fechas_reales = pd.to_datetime(df_vigencia['Fecha_Cuota_Vigente'], errors='coerce')
        
        df_vigencia['Estado_Vigencia_Agrupado'] = 'VIGENTES'
        mask_not_date = fechas_reales.isna()
        df_vigencia.loc[mask_not_date, 'Estado_Vigencia_Agrupado'] = df_vigencia.loc[mask_not_date, 'Fecha_Cuota_Vigente']
        
        df_vigencia['Estado_Vigencia_Agrupado'] = df_vigencia['Estado_Vigencia_Agrupado'].replace(
            {'': 'SIN ESTADO', 'nan': 'SIN ESTADO', 'NaN': 'SIN ESTADO', 'None': 'SIN ESTADO'}
        )

        df_vigencia['Sub_Estado_Vigencia'] = ''
        vigentes_mask = df_vigencia['Estado_Vigencia_Agrupado'] == 'VIGENTES'
    
        if vigentes_mask.any():
            fechas_vigentes = fechas_reales[vigentes_mask]
            subdivision_labels = fechas_vigentes.dt.day.apply(lambda d: f"Día {int(d)}" if pd.notna(d) else "")
            df_vigencia.loc[vigentes_mask, 'Sub_Estado_Vigencia'] = subdivision_labels

        agg_vigencia = df_vigencia.groupby(['Estado_Vigencia_Agrupado', 'Sub_Estado_Vigencia']).size().reset_index(name='count')

    return {
        "regional": agg_regional,
        "cobro": agg_cobro,
        "desembolso": agg_desembolso,
        "vigencia": agg_vigencia,
    }

def prepare_tab2_data(df_cartera, df_novedades):
    if df_cartera.empty:
        return {}
    
    df_cartera_activa = df_cartera.copy()

    # --- LÓGICA DE ESTADOS ACTUALIZADA ---
    # Separamos en 3: Anticipado, Pago y Sin Pago
    cond_anticipado = df_cartera_activa['Valor_Cuota_Vigente'].astype(str).str.strip().str.upper() == 'ANTICIPADO'
    cond_pago = df_cartera_activa['Total_Recaudo'] > 50000
    
    df_cartera_activa['Estado_Pago'] = np.select(
        [cond_anticipado, cond_pago], 
        ['ANTICIPADO', 'PAGO'], 
        default='SIN PAGO'
    )
    df_cartera_activa['Estado_Gestion'] = np.where(df_cartera_activa['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')

    agg_donut = df_cartera_activa['Estado_Pago'].value_counts()

    cargos_unicos_por_cliente = df_novedades[['Cedula_Cliente', 'Cargo_Usuario']].drop_duplicates() if not df_novedades.empty else pd.DataFrame(columns=['Cedula_Cliente', 'Cargo_Usuario'])
    df_merged = pd.merge(df_cartera_activa, cargos_unicos_por_cliente, on='Cedula_Cliente', how='left')
    df_merged['Cargo_Usuario'] = df_merged['Cargo_Usuario'].fillna('SIN CARGO')

    grouped_sunburst_inicial = df_merged.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped_sunburst_inicial = grouped_sunburst_inicial[~((grouped_sunburst_inicial['Estado_Gestion'] == 'CON GESTIÓN') & (grouped_sunburst_inicial['Cargo_Usuario'] == ''))]
    conteo_gestion_inicial = df_merged['Estado_Gestion'].value_counts()

    agg_rodamiento = None
    if 'Rodamiento' in df_cartera_activa.columns:
        agg_rodamiento = df_cartera_activa.groupby(['Rodamiento', 'Estado_Gestion'], observed=True).size().reset_index(name='Número de Cuentas')

    # --- TRES GRUPOS DE DETALLES ---
    df_pago = df_merged[df_merged['Estado_Pago'] == 'PAGO']
    df_sin_pago = df_merged[df_merged['Estado_Pago'] == 'SIN PAGO']
    df_anticipado = df_merged[df_merged['Estado_Pago'] == 'ANTICIPADO']

    grouped_detalle_pago = df_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped_detalle_sin_pago = df_sin_pago.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped_detalle_anticipado = df_anticipado.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')

    if not df_novedades.empty:
        novedades_por_cargo = df_novedades.groupby(['Cedula_Cliente', 'Cargo_Usuario']).size().reset_index(name='Novedades_Por_Cargo')
        columnas_clave = [
            'Cedula_Cliente', 'Empresa', 'Credito', 'Nombre_Cliente', 'Celular', 'Nombre_Ciudad', 'Zona',
            'Dias_Atraso_Final', 'Total_Recaudo', 'Valor_Vencido', 'Codeudor1', 'Nombre_Codeudor1', 
            'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2','Telefono_Codeudor2', 'Meta_$',
            'Estado_Pago', 'Estado_Gestion', 'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente'
        ]
        cols_finales_c = [c for c in columnas_clave if c in df_cartera_activa.columns]
        df_base_reducida = pd.merge(df_cartera_activa[cols_finales_c], novedades_por_cargo, on='Cedula_Cliente', how='left')
        df_para_tabla = pd.merge(df_base_reducida, df_novedades[['Cedula_Cliente', 'Cargo_Usuario', 'Novedad', 'Tipo_Novedad', 'Nombre_Usuario']], on=['Cedula_Cliente', 'Cargo_Usuario'], how='left')
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
        "detalle_anticipado": (grouped_detalle_anticipado, df_anticipado['Estado_Gestion'].value_counts()), # Añadimos Anticipados
        "processed_cartera": df_cartera_activa,
        "processed_data_merged": df_merged, 
        "data_para_tabla": df_para_tabla 
    }

def prepare_tab3_data(df):
    """      
    Agregación principal por Zona y Cobrador para Resultados.
    """
    franjas_a_usar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']    
    # Filtramos sin hacer .copy() inmediato
    mask_franjas = df['Franja_Meta'].isin(franjas_a_usar)
    mask_zonas = ~df['Zona'].isin(['CL1', 'CL2', 'CL3', 'CL4'])
    
    df_para_grupo = df[mask_franjas & mask_zonas]

    if df_para_grupo.empty:
        return {"resultados_zona": pd.DataFrame(), "resultados_cobrador": pd.DataFrame()}

    # Agregación por Zona (Sin conversiones redundantes)
    gb_zona = ['Regional_Cobro', 'Zona', 'Franja_Meta'] if 'Regional_Cobro' in df_para_grupo.columns else ['Zona', 'Franja_Meta']
    resultados_zona = df_para_grupo.groupby(gb_zona, observed=True).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Recaudo_Meta', 'sum'), 
        Recaudo_Sin_Anti_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Recaudo_Meta_Total=('Meta_T.R_$', 'sum'),
        Cant_Cuentas=('Zona', 'size')
    ).reset_index()

    resultados_zona['Cumplimiento_%'] = np.where(resultados_zona['Meta_Total'] > 0, resultados_zona['Recaudo_Total'] / resultados_zona['Meta_Total'], 0.0)

    # Agregación por Cobrador
    df_cobrador = df_para_grupo[df_para_grupo['Cobrador'].notna() & (df_para_grupo['Cobrador'] != '')]
    gb_cobrador = ['Regional_Cobro', 'Zona', 'Cobrador'] if 'Regional_Cobro' in df_para_grupo.columns else ['Zona', 'Cobrador']
    
    resultados_cobrador = df_cobrador.groupby(gb_cobrador, observed=True).agg(
        Meta_Total=('Meta_T.R_$', 'sum'),              
        Recaudo_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Cant_Cuentas=('Cobrador', 'size')
    ).reset_index()
    
    resultados_cobrador['Cumplimiento_%'] = np.where(resultados_cobrador['Meta_Total'] > 0, resultados_cobrador['Recaudo_Total'] / resultados_cobrador['Meta_Total'], 0.0)

    return {"resultados_zona": resultados_zona, "resultados_cobrador": resultados_cobrador}

def prepare_tab4_data(df_cartera, df_novedades):
    return {"cartera_para_mostrar": df_cartera, "novedades_para_mostrar": df_novedades}

def prepare_tab5_data(df_cartera):
    # Sin copias excesivas, y aprovechando que ya vienen numéricos del Parquet
    df_potenciales = df_cartera[(df_cartera['Dias_Atraso_Final'] <= 30) & (df_cartera['Total_Cuotas'] >= 6)].copy()
    
    if df_potenciales.empty:
        return {"potenciales_retanqueo": pd.DataFrame()}

    df_potenciales['Cuotas_Restantes'] = df_potenciales['Total_Cuotas'] - df_potenciales['Cuotas_Pagadas']
    
    cond_A = (df_potenciales['Total_Cuotas'].between(6, 8)) & (df_potenciales['Cuotas_Restantes'].between(1, 2))
    cond_B = (df_potenciales['Total_Cuotas'] > 8) & (df_potenciales['Cuotas_Restantes'].between(1, 4))
    
    return {"potenciales_retanqueo": df_potenciales[cond_A | cond_B]}