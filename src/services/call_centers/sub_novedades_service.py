import pandas as pd
import unicodedata
import difflib
import streamlit as st
from datetime import datetime, date 

def _normalize_name_set(series: pd.Series) -> pd.Series:
    """Normaliza nombres eliminando acentos y palabras comunes."""
    if series.empty: return series
    STOP_WORDS = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'i'}
    def normalize_string(name):
        if not isinstance(name, str): return set()
        name = ''.join(c for c in unicodedata.normalize('NFD', name.lower()) if unicodedata.category(c) != 'Mn')
        tokens = name.split()
        return {t for t in tokens if len(t) > 1 and t not in STOP_WORDS}
    return series.apply(normalize_string)

def process_novedades_system(df_novedades: pd.DataFrame, df_llamadas: pd.DataFrame) -> dict:
    """
    Procesa novedades, asigna Call Center y analiza COMPROMISOS DE PAGO.
    """
    resultado = {
        "df_detalle": pd.DataFrame(),
        "df_agg_call": pd.DataFrame(),
        "df_agg_tipo": pd.DataFrame(),
        "df_compromisos": pd.DataFrame(),
        "kpis": {"total": 0, "sin_asignar": 0, "top_tipo": "N/A"},
        "error": None
    }

    if df_novedades.empty or df_llamadas.empty:
        resultado["error"] = "Faltan datos de Novedades o Llamadas."
        return resultado

    # --- DETECCIÓN INTELIGENTE DE COLUMNAS ---
    def find_col(df, keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    col_usuario = find_col(df_novedades, ['nombre_usuario', 'usuario_novedad', 'usuario'])
    col_agente = find_col(df_llamadas, ['nombre_call', 'agente', 'nombre'])
    col_cc = find_col(df_llamadas, ['call_center', 'zona'])

    if not col_usuario: return {"error": "No se encontró columna de Usuario en Novedades", **resultado}
    if not col_agente: return {"error": "No se encontró columna de Agente en Llamadas", **resultado}

    try:
        # --- 1. FUZZY MATCHING (Asignación de Call Center) ---
        df_ref = df_llamadas[[col_agente, col_cc]].dropna().drop_duplicates()
        df_ref['tokens'] = _normalize_name_set(df_ref[col_agente])
        
        agentes_ref = []
        for row in df_ref.itertuples(index=False):
            # Usamos getattr para acceder dinámicamente por el nombre real de la columna
            cc_val = getattr(row, col_cc)
            tokens_val = getattr(row, 'tokens')
            if tokens_val:
                agentes_ref.append({'tokens': list(tokens_val), 'cc': cc_val, 'len': len(tokens_val)})

        def find_best_match(tokens_usuario_set):
            if not tokens_usuario_set: return 'SIN ASIGNAR'
            tokens_usuario = list(tokens_usuario_set)
            best_cc, best_score = 'SIN ASIGNAR', 0.0

            for agente in agentes_ref:
                tokens_agente, n_agente = agente['tokens'], agente['len']
                suma_similitud = 0.0
                for token_a in tokens_agente:
                    max_sim = 0.0
                    if token_a in tokens_usuario_set:
                        max_sim = 1.0
                    else:
                        for token_u in tokens_usuario:
                            sim = difflib.SequenceMatcher(None, token_a, token_u).ratio()
                            if sim > max_sim: max_sim = sim
                    if max_sim < 0.75: max_sim = 0.0
                    suma_similitud += max_sim
                
                score = suma_similitud / n_agente
                if score >= 0.75: return agente['cc'] # Match rápido más estricto
                if score > best_score: best_score, best_cc = score, agente['cc']
            
            return best_cc if best_score >= 0.60 else 'SIN ASIGNAR'

        df_proc = df_novedades.copy()
        df_proc['tokens_temp'] = _normalize_name_set(df_proc[col_usuario])
        df_proc['Call_Center_Asignado'] = df_proc['tokens_temp'].apply(find_best_match)
        
        valid_ccs = ['CL1', 'CL2', 'CL3', 'CL4', 'CL5', 'CL6', 'CL7', 'CL8', 'CL9']
        df_proc['Call_Center_Asignado'] = df_proc['Call_Center_Asignado'].apply(lambda x: x if x in valid_ccs else 'SIN ASIGNAR')
        # 1. Buscar columnas clave con flexibilidad
        col_tipo = find_col(df_proc, ['Tipo_Novedad', 'tipo']) or df_proc.columns[0]
        col_fecha_comp = find_col(df_proc, ['Fecha_Compromiso', 'compromiso'])

        # 2. Filtrado: Busca "COMPROMISO" en el texto
        mask_compromiso = df_proc[col_tipo].astype(str).str.contains("COMPROMISO", case=False, na=False)
        df_comp = df_proc[mask_compromiso].copy()

        if not df_comp.empty and col_fecha_comp:
            # 3. Limpieza de Fechas
            df_comp[col_fecha_comp] = df_comp[col_fecha_comp].astype(str).str.strip()
            
            # Convertimos a datetime
            df_comp['Fecha_Obj'] = pd.to_datetime(df_comp[col_fecha_comp], dayfirst=True, errors='coerce')
            
            hoy = pd.Timestamp.now().normalize()
            inicio_mes_actual = hoy.replace(day=1)

            def clasificar_acuerdo(fecha):
                if pd.isna(fecha): return 'FECHA INVÁLIDA'
                
                # Regla: No fechas anteriores al mes actual (ej: mes pasado es error)
                if fecha < inicio_mes_actual:
                    return 'FECHA INVÁLIDA' 
                
                # Regla: Fechas válidas pasadas vs futuras
                if fecha < hoy:
                    return 'ACUERDOS VENCIDOS'
                return 'ACUERDOS VIGENTES'

            df_comp['Estado_Acuerdo'] = df_comp['Fecha_Obj'].apply(clasificar_acuerdo)
            
            # Filtramos las inválidas para el gráfico, pero mantenemos VENCIDOS y VIGENTES
            df_chart = df_comp[df_comp['Estado_Acuerdo'].isin(['ACUERDOS VENCIDOS', 'ACUERDOS VIGENTES'])]
            
            if not df_chart.empty:
                df_compromisos = df_chart.groupby(['Call_Center_Asignado', 'Estado_Acuerdo']).size().reset_index(name='Cantidad')
            else:
                df_compromisos = pd.DataFrame()
                # Debug opcional: Si hay compromisos pero todas las fechas son inválidas
                if not df_comp.empty:
                    st.warning(f"Se encontraron {len(df_comp)} compromisos, pero todas sus fechas son inválidas o del mes pasado.")
        else:
            df_compromisos = pd.DataFrame()

        # ==============================================================================

        # Agregaciones finales (Aquí sí filtramos SIN ASIGNAR para las barras generales si quieres)
        mask_valid_cc = df_proc['Call_Center_Asignado'] != 'SIN ASIGNAR'
        df_agg_call = df_proc[mask_valid_cc].groupby('Call_Center_Asignado').size().reset_index(name='Cantidad')
        df_agg_tipo = df_proc[mask_valid_cc].groupby(['Call_Center_Asignado', col_tipo]).size().reset_index(name='Cantidad')

        resultado["df_detalle"] = df_proc.drop(columns=['tokens_temp'])
        resultado["df_agg_call"] = df_agg_call
        resultado["df_agg_tipo"] = df_agg_tipo
        resultado["df_compromisos"] = df_compromisos
        resultado["kpis"] = {
            "total": len(df_proc), 
            "sin_asignar": len(df_proc[~mask_valid_cc]), 
            "top_tipo": df_proc[col_tipo].mode()[0] if not df_proc.empty else "N/A"
        }
        
        return resultado

    except Exception as e:
        resultado["error"] = f"Error proceso: {str(e)}"
        return resultado