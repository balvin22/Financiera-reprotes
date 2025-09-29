# charts_retanqueos.py
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def prepare_retanqueos_data(df_cartera):
    """
    Filtra la cartera para encontrar clientes potenciales para retanqueo
    basado en las nuevas reglas de negocio especificadas.
    """
    # Nos aseguramos de trabajar con una copia y que las columnas necesarias sean numéricas
    df = df_cartera.copy()
    numeric_cols = ['Total_Cuotas', 'Cuotas_Pagadas', 'Dias_Atraso_Final']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Eliminamos filas donde los datos para el cálculo son nulos
    df.dropna(subset=numeric_cols, inplace=True)

    # --- INICIO DE LA NUEVA LÓGICA ---

    # 1. Condición base: Menos de 30 días de atraso
    df_potenciales = df[df['Dias_Atraso_Final'] <= 30].copy()

    # 2. Condición base 2: Solo créditos con 6 o más cuotas totales
    df_potenciales = df_potenciales[df_potenciales['Total_Cuotas'] >= 6].copy()

    # 3. Calcular cuotas restantes (solo para los que pasaron los filtros anteriores)
    df_potenciales['Cuotas_Restantes'] = df_potenciales['Total_Cuotas'] - df_potenciales['Cuotas_Pagadas']
    
    # 4. Aplicar las reglas de negocio específicas
    
    # Condición A: Créditos de 6 a 8 cuotas Y les faltan entre 1 y 2 por pagar
    condicion_A = (
        df_potenciales['Total_Cuotas'].between(6, 8) &
        df_potenciales['Cuotas_Restantes'].between(1, 2)
    )
    
    # Condición B: Créditos con más de 8 cuotas Y les faltan entre 1 y 4 por pagar
    condicion_B = (
        df_potenciales['Total_Cuotas'] > 8 &
        df_potenciales['Cuotas_Restantes'].between(1, 4)
    )
    
    # Combinamos las condiciones: un cliente es potencial si cumple A O B
    df_final = df_potenciales[condicion_A | condicion_B]
    
    # --- FIN DE LA NUEVA LÓGICA ---
    
    return df_final
