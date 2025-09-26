# charts_retanqueos.py
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def prepare_retanqueos_data(df_cartera):
    """
    Filtra la cartera para encontrar clientes potenciales para retanqueo
    basado en un conjunto de reglas de negocio.
    """
    # Nos aseguramos de trabajar con una copia y que las columnas necesarias sean numéricas
    df = df_cartera.copy()
    numeric_cols = ['Total_Cuotas', 'Cuotas_Pagadas', 'Dias_Atraso_Final']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Eliminamos filas donde los datos para el cálculo son nulos
    df.dropna(subset=numeric_cols, inplace=True)

    # 1. Condición base: Solo créditos al día
    df_potenciales = df[df['Dias_Atraso_Final'] <= 0].copy()

    # 2. Calcular cuotas restantes
    df_potenciales['Cuotas_Restantes'] = df_potenciales['Total_Cuotas'] - df_potenciales['Cuotas_Pagadas']
    
    # 3. Aplicar las reglas de negocio
    # Condición A: Créditos con 10 o más cuotas Y les faltan 3 o menos por pagar
    condicion_A = (df_potenciales['Total_Cuotas'] >= 10) & (df_potenciales['Cuotas_Restantes'] <= 3)
    
    # Condición B: Créditos con menos de 10 cuotas Y les faltan 2 o menos por pagar
    condicion_B = (df_potenciales['Total_Cuotas'] < 10) & (df_potenciales['Cuotas_Restantes'] <= 2)
    
    # Combinamos las condiciones: un cliente es potencial si cumple A O B
    df_final = df_potenciales[condicion_A | condicion_B]
    
    return df_final