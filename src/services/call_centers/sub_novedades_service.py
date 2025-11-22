import pandas as pd
import unicodedata
import difflib
import streamlit as st
from datetime import datetime, date 

def _normalize_name_set(series: pd.Series) -> pd.Series:
    if series.empty: return series
    STOP_WORDS = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'i'}
    def normalize_string(name):
        if not isinstance(name, str): return set()
        name = ''.join(c for c in unicodedata.normalize('NFD', name.lower()) if unicodedata.category(c) != 'Mn')
        tokens = name.split()
        return {t for t in tokens if len(t) > 1 and t not in STOP_WORDS}
    return series.apply(normalize_string)

def process_novedades_system(df_novedades: pd.DataFrame, df_llamadas: pd.DataFrame) -> dict:
    resultado = {
        "df_detalle": pd.DataFrame(),
        "df_agg_call": pd.DataFrame(),
        "df_agg_tipo": pd.DataFrame(),
        "df_compromisos": pd.DataFrame(),
        "kpis": {"total": 0, "sin_asignar": 0, "top_tipo": "N/A"},
        "error": None
    }

    if df_novedades.empty or df_llamadas.empty:
        resultado["error"] = "Faltan datos."
        return resultado

    # Limpieza
    df_novedades.columns = df_novedades.columns.str.strip()
    df_llamadas.columns = df_llamadas.columns.str.strip()

    col_usuario = 'Nombre_Usuario' if 'Nombre_Usuario' in df_novedades.columns else 'Usuario_Novedad'
    col_agente = 'Nombre_Call'
    col_cc = 'Call_Center'

    if col_usuario not in df_novedades.columns: return {"error": "Falta columna Usuario", **resultado}
    if col_agente not in df_llamadas.columns: return {"error": "Falta columna Agente", **resultado}

    try:
        # 1. Fuzzy Match
        df_ref = df_llamadas[[col_agente, col_cc]].dropna().drop_duplicates()
        df_ref['tokens'] = _normalize_name_set(df_ref[col_agente])
        
        agentes_ref = []
        for row in df_ref.itertuples():
            if row.tokens:
                agentes_ref.append({'tokens': list(row.tokens), 'cc': row.Call_Center, 'len': len(row.tokens)})

        def find_best_match(tokens_usuario_set):
            if not tokens_usuario_set: return 'SIN ASIGNAR'
            tokens_usuario = list(tokens_usuario_set)
            best_cc, best_score = 'SIN ASIGNAR', 0.0
            for agente in agentes_ref:
                tokens_agente, n_agente = agente['tokens'], agente['len']
                suma_similitud = 0.0
                for token_a in tokens_agente:
                    max_sim = 0.0
                    if token_a in tokens_usuario_set: max_sim = 1.0
                    else:
                        for token_u in tokens_usuario:
                            sim = difflib.SequenceMatcher(None, token_a, token_u).ratio()
                            if sim > max_sim: max_sim = sim
                    if max_sim < 0.75: max_sim = 0.0
                    suma_similitud += max_sim
                score = suma_similitud / n_agente
                if score >= 0.65: return agente['cc']
                if score > best_score: best_score, best_cc = score, agente['cc']
            return best_cc if best_score >= 0.60 else 'SIN ASIGNAR'

        df_proc = df_novedades.copy()
        df_proc['tokens_temp'] = _normalize_name_set(df_proc[col_usuario])
        df_proc['Call_Center_Asignado'] = df_proc['tokens_temp'].apply(find_best_match)
        
        valid_ccs = ['CL1', 'CL2', 'CL3', 'CL4', 'CL5', 'CL6', 'CL7', 'CL8', 'CL9']
        df_proc['Call_Center_Asignado'] = df_proc['Call_Center_Asignado'].apply(lambda x: x if x in valid_ccs else 'SIN ASIGNAR')


        col_tipo = 'Tipo_Novedad' if 'Tipo_Novedad' in df_proc.columns else df_proc.columns[0]
        col_fecha_comp = 'Fecha_Compromiso'
        
        mask_compromiso = df_proc[col_tipo].astype(str).str.contains("COMPROMISO", case=False, na=False)
        df_comp = df_proc[mask_compromiso].copy()

        if not df_comp.empty and col_fecha_comp in df_comp.columns:
            df_comp[col_fecha_comp] = df_comp[col_fecha_comp].astype(str).str.strip()
            df_comp['Fecha_Obj'] = pd.to_datetime(df_comp[col_fecha_comp], errors='coerce')
            
            hoy = pd.Timestamp.now().normalize()
            inicio_mes_actual = hoy.replace(day=1)

            def clasificar_acuerdo(fecha):
                if pd.isna(fecha): return 'ACUERDOS SIN FECHA'
                if fecha < inicio_mes_actual: return 'ACUERDOS SIN FECHA'
                if fecha < hoy: return 'ACUERDOS VENCIDOS'
                return 'ACUERDOS VIGENTES'

            df_comp['Estado_Acuerdo'] = df_comp['Fecha_Obj'].apply(clasificar_acuerdo)
            
            # --- [MODIFICACIÓN] FILTRAR 'SIN ASIGNAR' ---
            # Solo dejamos los registros que tienen un Call Center válido (CL1-CL9)
            df_comp_clean = df_comp[df_comp['Call_Center_Asignado'] != 'SIN ASIGNAR'].copy()
            
            # Agrupamos solo los válidos
            df_compromisos = df_comp_clean.groupby(['Call_Center_Asignado', 'Estado_Acuerdo']).size().reset_index(name='Cantidad')
        else:
            df_compromisos = pd.DataFrame()

        # ==============================================================================

        df_agg_call = df_proc[df_proc['Call_Center_Asignado'] != 'SIN ASIGNAR'].groupby('Call_Center_Asignado').size().reset_index(name='Cantidad')
        df_agg_tipo = df_proc[df_proc['Call_Center_Asignado'] != 'SIN ASIGNAR'].groupby(['Call_Center_Asignado', col_tipo]).size().reset_index(name='Cantidad')

        resultado["df_detalle"] = df_proc.drop(columns=['tokens_temp'])
        resultado["df_agg_call"] = df_agg_call
        resultado["df_agg_tipo"] = df_agg_tipo
        resultado["df_compromisos"] = df_compromisos
        resultado["kpis"] = {
            "total": len(df_proc), 
            "sin_asignar": len(df_proc[df_proc['Call_Center_Asignado'] == 'SIN ASIGNAR']), 
            "top_tipo": df_proc[col_tipo].mode()[0] if not df_proc.empty else "N/A"
        }
        return resultado
    except Exception as e:
        resultado["error"] = f"Error: {str(e)}"
        return resultado