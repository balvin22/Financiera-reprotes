import pandas as pd
import numpy as np
import streamlit as st

# --- Función Ayudante (Privada de este módulo) ---

def _calculate_llamadas_por_dia(df_llamadas_limpio: pd.DataFrame) -> pd.DataFrame:
    """Calcula la tendencia de llamadas por día, excluyendo fines de semana."""
    if 'Fecha_Llamada' not in df_llamadas_limpio.columns:
        st.warning("No se encontró la columna 'Fecha_Llamada' para el gráfico de tendencia.")
        return pd.DataFrame()
    try:
        df_temp = df_llamadas_limpio.copy()
        df_temp['Fecha_Dia'] = pd.to_datetime(df_temp['Fecha_Llamada']).dt.date
        
        # Excluir fines de semana (Sábado=5, Domingo=6)
        dias_semana = pd.to_datetime(df_temp['Fecha_Dia']).dt.dayofweek
        df_llamadas_habiles = df_temp[~dias_semana.isin([5, 6])].copy()
        
        if df_llamadas_habiles.empty:
            st.info("No se encontraron registros de llamadas en días hábiles para la tendencia.")
            return pd.DataFrame()
            
        df_llamadas_habiles['Estado_Respuesta'] = np.where(
            df_llamadas_habiles['Estado_Llamada'] == 'ANSWERED', 'CON RESPUESTA', 'SIN RESPUESTA'
        )
        
        df_llamadas_dia_agg = df_llamadas_habiles.groupby(['Fecha_Dia', 'Estado_Respuesta']).size().reset_index(name='Total_Llamadas')
        df_llamadas_dia_agg.rename(columns={'Fecha_Dia': 'Fecha'}, inplace=True)
        return df_llamadas_dia_agg
    except Exception as e:
        st.warning(f"Error procesando fechas para gráfico de llamadas por día: {e}")
        return pd.DataFrame()

# --- Función Principal (Pública de este módulo) ---

def process_llamadas(df_llamadas: pd.DataFrame) -> dict:
    """Procesa todas las estadísticas y DFs relacionados con las llamadas."""
    if df_llamadas.empty or 'Estado_Llamada' not in df_llamadas.columns:
        return {
            "llamadas_stats": {"total_llamadas": 0, "con_respuesta": 0, "sin_respuesta": 0},
            "df_grafico_llamadas": pd.DataFrame({"Tipo": ["CON RESPUESTA", "SIN RESPUESTA"], "Cantidad": [0, 0]}),
            "df_efectividad_call": pd.DataFrame(),
            "df_llamadas_por_dia": pd.DataFrame(),
            "alerta_umbral": 0
        }

    df_llamadas_limpio = df_llamadas.copy()
    df_llamadas_limpio['Estado_Llamada'] = df_llamadas_limpio['Estado_Llamada'].astype(str).str.strip().str.upper()
    
    total_llamadas = len(df_llamadas_limpio)
    con_respuesta = len(df_llamadas_limpio[df_llamadas_limpio['Estado_Llamada'] == 'ANSWERED'])
    sin_respuesta = total_llamadas - con_respuesta
    
    llamadas_stats = {
        "total_llamadas": total_llamadas,
        "con_respuesta": con_respuesta,
        "sin_respuesta": sin_respuesta
    }
    
    df_grafico_llamadas = pd.DataFrame({
        "Tipo": ["CON RESPUESTA", "SIN RESPUESTA"],
        "Cantidad": [con_respuesta, sin_respuesta]
    })
    
    df_efectividad_call = pd.DataFrame()
    try:
        # Asumiendo que 'Call_Center_Limpio' existe tras el filtrado
        agg_calls = df_llamadas_limpio.groupby('Call_Center_Limpio').agg(
            Total_Intentos=('Estado_Llamada', 'size'),
            Con_Respuesta=('Estado_Llamada', lambda x: (x == 'ANSWERED').sum())
        ).reset_index()
        agg_calls['Efectividad'] = np.where(agg_calls['Total_Intentos'] > 0, agg_calls['Con_Respuesta'] / agg_calls['Total_Intentos'], 0)
        agg_calls.rename(columns={'Call_Center_Limpio': 'Call_Center'}, inplace=True)
        df_efectividad_call = agg_calls.sort_values(by='Efectividad', ascending=False)
    except Exception as e:
        st.error(f"Error calculando efectividad de llamadas: {e}")
        df_efectividad_call = pd.DataFrame()

    alerta_umbral = 0
    if 'Call_Center_Limpio' in df_llamadas_limpio.columns:
        n_call_centers = df_llamadas_limpio['Call_Center_Limpio'].nunique()
        if n_call_centers > 0:
            alerta_umbral = n_call_centers * 30
            
    df_llamadas_por_dia = _calculate_llamadas_por_dia(df_llamadas_limpio)
    
    return {
        "llamadas_stats": llamadas_stats,
        "df_grafico_llamadas": df_grafico_llamadas,
        "df_efectividad_call": df_efectividad_call,
        "df_llamadas_por_dia": df_llamadas_por_dia,
        "alerta_umbral": alerta_umbral
    }