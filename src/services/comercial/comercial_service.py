# comercial_service.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False)
def prepare_tab5_data(df_cartera, df_fnz):
    """
    Procesa la cartera para:
    1. Identificar clientes potenciales para retanqueo.
    2. Identificar seguimiento de nuevos créditos (Cosechas recientes).
    """
    # --- PARTE 1: RETANQUEO (Tu lógica existente) ---
    df = df_cartera.copy()
    
    numeric_cols = ['Total_Cuotas', 'Cuotas_Pagadas', 'Dias_Atraso_Final']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df.dropna(subset=numeric_cols, inplace=True)
    
    # Filtro retanqueo
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
    df_retanqueo = df_potenciales[condicion_A | condicion_B]
    
    # Limpieza FNZ
    if not df_fnz.empty:
        cols_clave = ['Estado', 'Analista_Asociado', 'Regional_Venta', 'Nombre_Vendedor']
        for col in cols_clave:
            if col in df_fnz.columns:
                df_fnz[col] = df_fnz[col].astype(str).str.strip().fillna("Sin Información")

    # --- PARTE 2: NUEVA LÓGICA DE CRÉDITOS NUEVOS (COSECHAS) ---
    # Usamos el df original (df_cartera) pero aseguramos tipos
    df_nuevos = df_cartera.copy()
    
    # Conversiones necesarias
    df_nuevos['Fecha_Desembolso'] = pd.to_datetime(df_nuevos['Fecha_Desembolso'], errors='coerce')
    cols_num_nuevos = ['Cuotas_Pagadas', 'Dias_Atraso_Final', 'Valor_Vencido', 'Total_Cuotas']
    for col in cols_num_nuevos:
        df_nuevos[col] = pd.to_numeric(df_nuevos[col], errors='coerce').fillna(0)

    # 1. Filtro de tiempo: Últimos 6 meses
    fecha_actual = datetime.now()
    fecha_corte_6_meses = fecha_actual - timedelta(days=180)
    
    df_cosechas = df_nuevos[
        (df_nuevos['Fecha_Desembolso'] >= fecha_corte_6_meses) &
        (df_nuevos['Dias_Atraso_Final'] > 0) # Solo los que tienen mora, que es lo que quieres gestionar
    ].copy()

    # 2. Segmentación en 3 grupos
    condiciones = [
        (df_cosechas['Cuotas_Pagadas'] == 0), # No pagó la primera
        (df_cosechas['Cuotas_Pagadas'] == 1), # Pagó 1ra, debe la 2da
        (df_cosechas['Cuotas_Pagadas'].between(2, 5)) # Pagó 1ra y 2da, debe de 3ra en adelante
    ]
    etiquetas = [
        'SECCION_1_SIN_PAGO',
        'SECCION_2_FALLO_2DA',
        'SECCION_3_FALLO_3RA_PLUS'
    ]
    
    df_cosechas['Grupo_Seguimiento'] = np.select(condiciones, etiquetas, default='OTROS')
    
    # Filtramos para quitar 'OTROS' (los que van al día o tienen más de 6 pagadas)
    df_cosechas = df_cosechas[df_cosechas['Grupo_Seguimiento'] != 'OTROS']

    return {
        "potenciales_retanqueo": df_retanqueo,
        "data_fnz": df_fnz,
        "data_cosechas": df_cosechas # <--- Nuevo DataFrame agregado al retorno
    }