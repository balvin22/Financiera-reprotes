import pandas as pd
import numpy as np
import unicodedata
import difflib
import streamlit as st

def _normalize_name_tuple(series: pd.Series) -> pd.Series:
    if series.empty: return series
    STOP_WORDS = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'i'}
    
    def normalize_string(name):
        if pd.isna(name) or str(name).lower() in ['nan', 'none', '']: 
            return tuple()
        name = str(name)
        name = ''.join(c for c in unicodedata.normalize('NFD', name.lower()) if unicodedata.category(c) != 'Mn')
        return tuple(t for t in name.split() if len(t) > 1 and t not in STOP_WORDS)
    
    return series.astype(str).apply(normalize_string)

def process_novedades_system(df_novedades: pd.DataFrame, df_llamadas: pd.DataFrame) -> dict:
    resultado = {
        "df_detalle": pd.DataFrame(), "df_agg_call": pd.DataFrame(), "df_agg_tipo": pd.DataFrame(),
        "df_compromisos": pd.DataFrame(), "kpis": {"total": 0, "sin_asignar": 0, "top_tipo": "N/A"}, "error": None
    }

    if df_novedades.empty:
        return {**resultado, "error": "No hay datos de novedades."}

    df_novedades.columns = df_novedades.columns.str.strip()
    if not df_llamadas.empty:
        df_llamadas.columns = df_llamadas.columns.str.strip()

    col_usuario = 'Nombre_Usuario' if 'Nombre_Usuario' in df_novedades.columns else 'Usuario_Novedad'
    col_agente = 'Nombre_Call'
    col_cc = 'Call_Center'
    col_tipo = 'Tipo_Novedad'
    col_fecha_comp = 'Fecha_Compromiso'

    if col_usuario not in df_novedades.columns: 
        return {**resultado, "error": f"Falta la columna '{col_usuario}'"}

    try:
        usuarios_unicos = df_novedades[col_usuario].dropna().unique()
        df_unicos_nov = pd.DataFrame({col_usuario: usuarios_unicos})
        df_unicos_nov['tokens_temp'] = _normalize_name_tuple(df_unicos_nov[col_usuario])

        agentes_ref = []
        if not df_llamadas.empty and col_agente in df_llamadas.columns and col_cc in df_llamadas.columns:
            df_ref = df_llamadas[[col_agente, col_cc]].dropna().drop_duplicates()
            df_ref['tokens'] = _normalize_name_tuple(df_ref[col_agente])
            agentes_ref = [{'tokens': list(r.tokens), 'cc': r.Call_Center, 'len': len(r.tokens)} for r in df_ref.itertuples() if r.tokens]

        def find_best_match(tokens_usuario_tuple):
            if not tokens_usuario_tuple or not agentes_ref: return 'SIN ASIGNAR'
            best_cc, best_score = 'SIN ASIGNAR', 0.0
            
            for agente in agentes_ref:
                suma_similitud = sum(
                    1.0 if t_a in tokens_usuario_tuple else max((difflib.SequenceMatcher(None, t_a, t_u).ratio() for t_u in tokens_usuario_tuple), default=0.0)
                    for t_a in agente['tokens']
                )
                score = suma_similitud / agente['len'] if agente['len'] > 0 else 0
                if score >= 0.65: return agente['cc']
                if score > best_score: best_score, best_cc = score, agente['cc']
                
            return best_cc if best_score >= 0.60 else 'SIN ASIGNAR'

        df_unicos_nov['Call_Center_Asignado'] = df_unicos_nov['tokens_temp'].apply(find_best_match)
        
        valid_ccs = {'CL1', 'CL2', 'CL3', 'CL4', 'CL5', 'CL6', 'CL7', 'CL8', 'CL9'}
        df_unicos_nov['Call_Center_Asignado'] = df_unicos_nov['Call_Center_Asignado'].apply(lambda x: x if x in valid_ccs else 'SIN ASIGNAR')
        
        mapa_asignacion = dict(zip(df_unicos_nov[col_usuario], df_unicos_nov['Call_Center_Asignado']))
        
        df_proc = df_novedades.copy()
        df_proc['Call_Center_Asignado'] = df_proc[col_usuario].map(mapa_asignacion).fillna('SIN ASIGNAR')

        # --- LÓGICA DE COMPROMISOS ---
        df_compromisos = pd.DataFrame()
        
        if col_tipo not in df_proc.columns:
            st.error(f"🔴 ALERTA: No existe la columna '{col_tipo}' en el archivo procesado.")
        elif col_fecha_comp not in df_proc.columns:
            st.error(f"🔴 ALERTA: No existe la columna '{col_fecha_comp}' en el archivo procesado.")
        else:
            df_proc['Tipo_Limpio'] = df_proc[col_tipo].astype(str).str.strip().str.upper()
            
            mask_compromiso = df_proc['Tipo_Limpio'].str.contains("COMPROMISO", na=False)
            df_comp = df_proc[mask_compromiso].copy()

            if not df_comp.empty:
                hoy = pd.Timestamp.now().normalize()
                inicio_mes_actual = hoy.replace(day=1)
                
                fechas_obj = pd.to_datetime(df_comp[col_fecha_comp], errors='coerce')
                
                condiciones = [
                    fechas_obj.isna() | (fechas_obj < inicio_mes_actual),
                    fechas_obj < hoy
                ]
                elecciones = ['ACUERDOS SIN FECHA', 'ACUERDOS VENCIDOS']
                estados_acuerdo = np.select(condiciones, elecciones, default='ACUERDOS VIGENTES')
                
                df_comp['Estado_Acuerdo'] = estados_acuerdo
                
                # --- AQUÍ QUITAMOS LOS 'SIN ASIGNAR' ANTES DE GRAFICAR ---
                df_comp_limpio = df_comp[df_comp['Call_Center_Asignado'] != 'SIN ASIGNAR']
                
                # Agrupamos solo los válidos
                df_compromisos = df_comp_limpio.groupby(['Call_Center_Asignado', 'Estado_Acuerdo'], observed=False).size().reset_index(name='Cantidad')

        # --- AGRUPACIONES FINALES ---
        mask_asignados = df_proc['Call_Center_Asignado'] != 'SIN ASIGNAR'
        df_agg_call = df_proc[mask_asignados].groupby('Call_Center_Asignado', observed=False).size().reset_index(name='Cantidad')
        
        df_agg_tipo = pd.DataFrame()
        top_tipo = "N/A"
        if col_tipo in df_proc.columns:
            df_agg_tipo = df_proc[mask_asignados].groupby(['Call_Center_Asignado', col_tipo], observed=False).size().reset_index(name='Cantidad')
            if not df_proc.empty:
                top_tipo = df_proc[col_tipo].mode()[0]

        resultado.update({
            "df_detalle": df_proc, "df_agg_call": df_agg_call, "df_agg_tipo": df_agg_tipo, "df_compromisos": df_compromisos,
            "kpis": {"total": len(df_proc), "sin_asignar": (~mask_asignados).sum(), "top_tipo": top_tipo}
        })
        return resultado
    except Exception as e:
        import traceback
        st.error(f"Error crítico en sistema de novedades: {str(e)} \n {traceback.format_exc()}")
        return resultado