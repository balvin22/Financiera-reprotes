import pandas as pd
import numpy as np
import streamlit as st

def _normalize_telefonos(series: pd.Series) -> pd.Series:
    """Normaliza una serie de teléfonos a string, quitando nulos y el molesto '.0' de Pandas."""
    return series.dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

def process_mensajeria_funnel(df_mensajeria: pd.DataFrame, df_novedades: pd.DataFrame, df_cartera: pd.DataFrame) -> dict:
    if df_mensajeria.empty:
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}

    try:
        total_mensajes = len(df_mensajeria)
        
        if 'Tipo_Respuesta_Agente' in df_mensajeria.columns:
            es_conversacion = df_mensajeria['Tipo_Respuesta_Agente'].astype(str).str.lower().str.strip().isin(['text', 'audio'])
        else:
            es_conversacion = pd.Series([False] * total_mensajes, index=df_mensajeria.index)

        df_conversaciones = df_mensajeria[es_conversacion].copy()
        total_conversaciones = len(df_conversaciones)

        df_efectividad_mensajeria = pd.DataFrame()
        if 'Call_Center' in df_mensajeria.columns:
            agg_msgs = df_mensajeria.groupby('Call_Center', observed=True).size().reset_index(name='Total_Entregados')
            
            if total_conversaciones > 0:
                conv_counts = df_conversaciones.groupby('Call_Center', observed=True).size().reset_index(name='Total_Conversaciones')
                agg_msgs = agg_msgs.merge(conv_counts, on='Call_Center', how='left')
                agg_msgs['Total_Conversaciones'] = agg_msgs['Total_Conversaciones'].fillna(0)
            else:
                agg_msgs['Total_Conversaciones'] = 0
                
            agg_msgs['Efectividad'] = np.where(agg_msgs['Total_Entregados'] > 0, agg_msgs['Total_Conversaciones'] / agg_msgs['Total_Entregados'], 0)
            df_efectividad_mensajeria = agg_msgs.sort_values(by='Efectividad', ascending=False)

        total_gestion_sistema, total_clientes_pago = 0, 0
        
        # --- CRUCE 1: Gestión en Sistema ---
        if not df_conversaciones.empty and not df_novedades.empty and 'Numero_Telefono' in df_conversaciones.columns:
            tel_nov = set()
            if 'Telefono_Cliente' in df_novedades.columns:
                tel_nov.update(_normalize_telefonos(df_novedades['Telefono_Cliente']))
            if 'Celular_Cliente' in df_novedades.columns:
                tel_nov.update(_normalize_telefonos(df_novedades['Celular_Cliente']))
            
            df_conversaciones['Numero_Telefono_Norm'] = _normalize_telefonos(df_conversaciones['Numero_Telefono'])
            
            df_gestion_sistema = df_conversaciones[df_conversaciones['Numero_Telefono_Norm'].isin(tel_nov)]
            total_gestion_sistema = len(df_gestion_sistema)

        # --- CRUCE 2: Clientes con Pago (CORREGIDO) ---
        if total_gestion_sistema > 0 and not df_cartera.empty:
            # 1. Extraemos las cédulas con pago de la cartera y LAS LIMPIAMOS
            if 'Estado_Pago' in df_cartera.columns:
                df_pagos = df_cartera[df_cartera['Estado_Pago'] == 'PAGO']
            elif 'Total_Recaudo' in df_cartera.columns:
                df_pagos = df_cartera[pd.to_numeric(df_cartera['Total_Recaudo'], errors='coerce').fillna(0) > 0]
            else:
                df_pagos = pd.DataFrame()

            # Aseguramos que la cédula sea un texto limpio sin ".0"
            if not df_pagos.empty and 'Cedula_Cliente' in df_pagos.columns:
                cedulas_con_pago = set(df_pagos['Cedula_Cliente'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip())
            else:
                cedulas_con_pago = set()
            
            # 2. Mapeo Robusto de Teléfono -> Cédula (Sin usar to_dict)
            map_tel_a_cedula = {}
            df_novedades_clean = df_novedades.dropna(subset=['Cedula_Cliente']).copy()
            df_novedades_clean['Cedula_Cliente'] = df_novedades_clean['Cedula_Cliente'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            for col in ['Telefono_Cliente', 'Celular_Cliente']:
                if col in df_novedades_clean.columns:
                    valid_rows = df_novedades_clean.dropna(subset=[col])
                    telefonos_norm = _normalize_telefonos(valid_rows[col])
                    cedulas_norm = valid_rows['Cedula_Cliente']
                    
                    # Emparejamos uno a uno evitando nulos
                    for tel, ced in zip(telefonos_norm, cedulas_norm):
                        if tel and tel != 'nan':
                            map_tel_a_cedula[tel] = ced

            # 3. Cruzamos e identificamos pagos
            cedulas_gestionadas = df_gestion_sistema['Numero_Telefono_Norm'].map(map_tel_a_cedula)
            # Quitamos los nulos del mapeo antes de comparar
            cedulas_gestionadas_limpias = cedulas_gestionadas.dropna()
            total_clientes_pago = cedulas_gestionadas_limpias.isin(cedulas_con_pago).sum()

        df_funnel_mensajeria = pd.DataFrame({
            'Etapa': ['Mensajes Entregados', 'Conversaciones', 'Gestión en Sistema', 'Clientes con Pago'],
            'Cantidad': [total_mensajes, total_conversaciones, total_gestion_sistema, total_clientes_pago]
        })

        return {"df_funnel_mensajeria": df_funnel_mensajeria, "df_efectividad_mensajeria": df_efectividad_mensajeria}

    except Exception as e:
        st.error(f"Error procesando la data de mensajería: {str(e)}")
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}