import pandas as pd
import numpy as np
import streamlit as st

# --- Función Ayudante (Privada de este módulo) ---

def _calculate_llamadas_por_dia(df_llamadas_limpio: pd.DataFrame) -> pd.DataFrame:
    """Calcula la tendencia de llamadas por día, excluyendo fines de semana."""
    if 'Fecha_Llamada' not in df_llamadas_limpio.columns:
        return pd.DataFrame()
    
    try:
        # Extraemos solo lo necesario y borramos nulos
        df_temp = df_llamadas_limpio[['Fecha_Llamada', 'Estado_Llamada']].dropna()
        if df_temp.empty: 
            return pd.DataFrame()
        
        # Como es datetime desde el data_loader, extraemos el día directo
        dias_semana = df_temp['Fecha_Llamada'].dt.dayofweek
        
        # Excluir fines de semana (Sábado=5, Domingo=6)
        df_llamadas_habiles = df_temp[~dias_semana.isin([5, 6])].copy()
        
        if df_llamadas_habiles.empty:
            return pd.DataFrame()
            
        df_llamadas_habiles['Fecha_Dia'] = df_llamadas_habiles['Fecha_Llamada'].dt.date
        df_llamadas_habiles['Estado_Respuesta'] = np.where(
            df_llamadas_habiles['Estado_Llamada'] == 'ANSWERED', 'CON RESPUESTA', 'SIN RESPUESTA'
        )
        
        df_llamadas_dia_agg = df_llamadas_habiles.groupby(['Fecha_Dia', 'Estado_Respuesta'], observed=True).size().reset_index(name='Total_Llamadas')
        df_llamadas_dia_agg.rename(columns={'Fecha_Dia': 'Fecha'}, inplace=True)
        return df_llamadas_dia_agg
    except Exception as e:
        return pd.DataFrame()

# --- Función Principal (Pública de este módulo) ---

def process_llamadas(df_llamadas: pd.DataFrame) -> dict:
    """Procesa todas las estadísticas y DFs relacionados con las llamadas."""
    
    # Preparamos un retorno vacío por si no hay datos válidos
    resultado_vacio = {
        "llamadas_stats": {"total_llamadas": 0, "con_respuesta": 0, "sin_respuesta": 0},
        "df_grafico_llamadas": pd.DataFrame({"Tipo": ["CON RESPUESTA", "SIN RESPUESTA"], "Cantidad": [0, 0]}),
        "df_efectividad_call": pd.DataFrame(),
        "df_llamadas_por_dia": pd.DataFrame(),
        "alerta_umbral": 0
    }

    if df_llamadas.empty or 'Estado_Llamada' not in df_llamadas.columns:
        return resultado_vacio

    # =========================================================================
    # FILTRO MAESTRO: Cortar de raíz los NAN y valores vacíos
    # =========================================================================
    if 'Call_Center_Limpio' in df_llamadas.columns:
        # 1. Convertimos a texto
        # 2. .str.strip() -> Elimina espacios invisibles antes o después (ej: " NAN ")
        # 3. .str.upper() -> Pone todo en mayúsculas
        cc_temp = df_llamadas['Call_Center_Limpio'].astype(str).str.strip().str.upper()
        
        # 4. Creamos una máscara que rechaza cualquier variación de dato inválido
        mask_validos = ~cc_temp.isin(['NAN', 'NONE', 'NULL', '', '<NA>'])
        
        # 5. Sobrescribimos el DataFrame solo con los reales
        df_llamadas = df_llamadas[mask_validos].copy()

    # Si después de limpiar los fantasmas nos quedamos sin datos, retornamos ceros
    if df_llamadas.empty:
        return resultado_vacio

    # Cálculos de KPIs generales (Ahora libres de NANs)
    total_llamadas = len(df_llamadas)
    con_respuesta = (df_llamadas['Estado_Llamada'] == 'ANSWERED').sum()
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
    if 'Call_Center_Limpio' in df_llamadas.columns:
        try:
            # Agrupamos directo porque ya limpiamos arriba
            agg_calls = df_llamadas.groupby('Call_Center_Limpio', observed=True).agg(
                Total_Intentos=('Estado_Llamada', 'size'),
                Con_Respuesta=('Estado_Llamada', lambda x: (x == 'ANSWERED').sum())
            ).reset_index()
            
            agg_calls['Efectividad'] = np.where(agg_calls['Total_Intentos'] > 0, agg_calls['Con_Respuesta'] / agg_calls['Total_Intentos'], 0)
            df_efectividad_call = agg_calls.rename(columns={'Call_Center_Limpio': 'Call_Center'}).sort_values(by='Efectividad', ascending=False)
        except Exception as e:
            st.error(f"Error calculando efectividad de llamadas: {e}")
            df_efectividad_call = pd.DataFrame()

    alerta_umbral = df_llamadas['Call_Center_Limpio'].nunique() * 30 if 'Call_Center_Limpio' in df_llamadas.columns else 0
    df_llamadas_por_dia = _calculate_llamadas_por_dia(df_llamadas)
    
    return {
        "llamadas_stats": llamadas_stats,
        "df_grafico_llamadas": df_grafico_llamadas,
        "df_efectividad_call": df_efectividad_call,
        "df_llamadas_por_dia": df_llamadas_por_dia,
        "alerta_umbral": alerta_umbral
    }