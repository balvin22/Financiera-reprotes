# comercial_service.py
import streamlit as st
import pandas as pd

@st.cache_data(show_spinner=False)
def prepare_tab5_data(df_cartera):
    """
    Procesa la cartera para identificar clientes potenciales para retanqueo
    basado en el comportamiento de pago y cuotas restantes.
    """
    # Trabajamos sobre una copia para no alterar el dataframe original
    df = df_cartera.copy()
    
    # Convertir columnas numéricas y limpiar errores
    numeric_cols = ['Total_Cuotas', 'Cuotas_Pagadas', 'Dias_Atraso_Final']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Eliminar filas donde los datos clave sean nulos
    df.dropna(subset=numeric_cols, inplace=True)
    
    # Filtro inicial: Clientes al día (o con poco atraso) y créditos con cierta madurez
    df_potenciales = df[df['Dias_Atraso_Final'] <= 30].copy()
    df_potenciales = df_potenciales[df_potenciales['Total_Cuotas'] >= 6].copy()
    
    # Calcular cuotas restantes
    df_potenciales['Cuotas_Restantes'] = df_potenciales['Total_Cuotas'] - df_potenciales['Cuotas_Pagadas']
    
    # Definir condiciones de negocio para el retanqueo
    condicion_A = (
        (df_potenciales['Total_Cuotas'].between(6, 8)) &
        (df_potenciales['Cuotas_Restantes'].between(1, 2))
    )
    
    condicion_B = (
        (df_potenciales['Total_Cuotas'] > 8) &
        (df_potenciales['Cuotas_Restantes'].between(1, 4))
    )
    
    # Aplicar filtros finales
    df_final = df_potenciales[condicion_A | condicion_B]
    
    return {
        "potenciales_retanqueo": df_final
    }