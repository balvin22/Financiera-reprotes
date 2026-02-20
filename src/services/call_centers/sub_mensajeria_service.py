import pandas as pd
import numpy as np
import streamlit as st

# --- Función Ayudante ---
def _normalize_telefonos(series: pd.Series) -> pd.Series:
    """Normaliza una serie de teléfonos a string, quitando nulos y '.0'."""
    return series.dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# --- Función Principal ---
def process_mensajeria_funnel(df_mensajeria: pd.DataFrame, df_novedades: pd.DataFrame, df_cartera: pd.DataFrame) -> dict:
    """Procesa el embudo de conversión usando la nueva columna 'Tipo_Respuesta_Agente'."""
    
    if df_mensajeria.empty or df_novedades.empty or df_cartera.empty:
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}

    try:
        df_mensajeria_limpio = df_mensajeria.copy()
        total_mensajes = len(df_mensajeria_limpio)
        
        # --- Paso 1: Identificar Conversaciones con la nueva lógica ---
        if 'Tipo_Respuesta_Agente' in df_mensajeria_limpio.columns:
            # Limpiamos la columna para evitar errores de formato
            df_mensajeria_limpio['Tipo_Respuesta_Agente'] = df_mensajeria_limpio['Tipo_Respuesta_Agente'].astype(str).str.lower().str.strip()
            
            # Nueva lógica: 'text' o 'audio' implica conversación
            df_mensajeria_limpio['Es_Conversacion'] = np.where(
                df_mensajeria_limpio['Tipo_Respuesta_Agente'].isin(['text', 'audio']), 1, 0
            )
        else:
            st.error("❌ La columna 'Tipo_Respuesta_Agente' no existe en el reporte de mensajería.")
            df_mensajeria_limpio['Es_Conversacion'] = 0

        df_conversaciones = df_mensajeria_limpio[df_mensajeria_limpio['Es_Conversacion'] == 1].copy()
        total_conversaciones = len(df_conversaciones)

        # --- Paso 2: Efectividad por Call Center ---
        df_efectividad_mensajeria = pd.DataFrame()
        if 'Call_Center' in df_mensajeria_limpio.columns:
            agg_msgs = df_mensajeria_limpio.groupby('Call_Center').agg(
                Total_Entregados=('Call_Center', 'size'),
                Total_Conversaciones=('Es_Conversacion', 'sum')
            ).reset_index()
            
            agg_msgs['Efectividad'] = np.where(
                agg_msgs['Total_Entregados'] > 0, 
                agg_msgs['Total_Conversaciones'] / agg_msgs['Total_Entregados'], 
                0
            )
            df_efectividad_mensajeria = agg_msgs.sort_values(by='Efectividad', ascending=False)

        # --- Paso 3: Gestión en Sistema (Cruce por Teléfonos) ---
        total_gestion_sistema = 0
        df_gestion_sistema = pd.DataFrame()
        
        if not df_conversaciones.empty and 'Numero_Telefono' in df_conversaciones.columns:
            # Extraer set de teléfonos únicos de novedades (Celular + Teléfono)
            telefonos_novedades = set(_normalize_telefonos(df_novedades.get('Telefono_Cliente', pd.Series(dtype=str))))
            telefonos_novedades.update(_normalize_telefonos(df_novedades.get('Celular_Cliente', pd.Series(dtype=str))))
            
            df_conversaciones['Numero_Telefono_Norm'] = _normalize_telefonos(df_conversaciones['Numero_Telefono'])
            df_gestion_sistema = df_conversaciones[df_conversaciones['Numero_Telefono_Norm'].isin(telefonos_novedades)].copy()
            total_gestion_sistema = len(df_gestion_sistema)

        # --- Paso 4: Clientes con Pago (Cruce por Cédula) ---
        total_clientes_pago = 0
        if not df_gestion_sistema.empty:
            # Usar la lógica de 'Total_Recaudo' o un flag de estado si lo tienes
            # Según tu código anterior, buscamos 'Estado_Pago' == 'PAGO'
            if 'Estado_Pago' in df_cartera.columns:
                cedulas_con_pago = set(df_cartera[df_cartera['Estado_Pago'] == 'PAGO']['Cedula_Cliente'].astype(str))
            else:
                # Si no existe 'Estado_Pago', podrías usar Total_Recaudo > 0 como fallback
                cedulas_con_pago = set(df_cartera[df_cartera['Total_Recaudo'] > 0]['Cedula_Cliente'].astype(str))
            
            # Mapeo de Teléfono -> Cédula usando el archivo de Novedades
            df_novedades_map = df_novedades.dropna(subset=['Cedula_Cliente']).copy()
            map_tel_a_cedula = {}
            
            for col_tel in ['Telefono_Cliente', 'Celular_Cliente']:
                if col_tel in df_novedades_map.columns:
                    df_novedades_map['tmp_tel'] = _normalize_telefonos(df_novedades_map[col_tel])
                    map_tel_a_cedula.update(df_novedades_map.set_index('tmp_tel')['Cedula_Cliente'].astype(str).to_dict())

            df_gestion_sistema['Cedula_Mapeada'] = df_gestion_sistema['Numero_Telefono_Norm'].map(map_tel_a_cedula)
            total_clientes_pago = df_gestion_sistema['Cedula_Mapeada'].isin(cedulas_con_pago).sum()

        # Construcción del DataFrame del Funnel
        data_funnel = {
            'Etapa': [
                'Mensajes Entregados', 
                'Conversaciones', 
                'Gestión en Sistema',  
                'Clientes con Pago'    
            ],
            'Cantidad': [
                total_mensajes, 
                total_conversaciones, 
                total_gestion_sistema, 
                total_clientes_pago
            ]
        }
        df_funnel_mensajeria = pd.DataFrame(data_funnel)

        return {
            "df_funnel_mensajeria": df_funnel_mensajeria,
            "df_efectividad_mensajeria": df_efectividad_mensajeria
        }

    except Exception as e:
        st.error(f"Error al procesar el embudo de mensajería: {e}")
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}