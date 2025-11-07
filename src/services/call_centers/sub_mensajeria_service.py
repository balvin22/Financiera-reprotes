import pandas as pd
import numpy as np
import streamlit as st

# --- Función Ayudante (Privada de este módulo) ---

def _normalize_telefonos(series: pd.Series) -> pd.Series:
    """Normaliza una serie de teléfonos a string, quitando nulos y '.0'."""
    return series.dropna().astype(str).str.replace(r'\.0$', '', regex=True)

# --- Función Principal (Pública de este módulo) ---

def process_mensajeria_funnel(df_mensajeria: pd.DataFrame, df_novedades: pd.DataFrame, df_cartera: pd.DataFrame) -> dict:
    """Procesa el embudo de conversión de mensajería y la efectividad."""
    if df_mensajeria.empty or df_novedades.empty or df_cartera.empty:
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}

    try:
        # --- Paso 1 y 2: Entregados, Conversaciones y Efectividad ---
        df_mensajeria_limpio = df_mensajeria.copy()
        total_mensajes = len(df_mensajeria_limpio)
        total_conversaciones = 0
        df_conversaciones = pd.DataFrame()
        df_efectividad_mensajeria = pd.DataFrame()

        if 'Primer_Mensaje_Agente' in df_mensajeria_limpio.columns:
            df_mensajeria_limpio['Primer_Mensaje_Agente'] = df_mensajeria_limpio['Primer_Mensaje_Agente'].astype(str).replace('nan', '')
            df_mensajeria_limpio['Es_Conversacion'] = np.where(
                df_mensajeria_limpio['Primer_Mensaje_Agente'].notna() &
                (df_mensajeria_limpio['Primer_Mensaje_Agente'] != '') &
                (df_mensajeria_limpio['Primer_Mensaje_Agente'] != 'None'), 1, 0
            )
            df_conversaciones = df_mensajeria_limpio[df_mensajeria_limpio['Es_Conversacion'] == 1].copy()
            total_conversaciones = len(df_conversaciones)
        else:
            st.warning("Columna 'Primer_Mensaje_Agente' no encontrada en datos de mensajería.")

        if 'Call_Center' in df_mensajeria_limpio.columns:
            agg_msgs = df_mensajeria_limpio.groupby('Call_Center').agg(
                Total_Entregados=('Primer_Mensaje_Agente', 'size'),
                Total_Conversaciones=('Es_Conversacion', 'sum')
            ).reset_index()
            agg_msgs['Efectividad'] = np.where(agg_msgs['Total_Entregados'] > 0, agg_msgs['Total_Conversaciones'] / agg_msgs['Total_Entregados'], 0)
            df_efectividad_mensajeria = agg_msgs.sort_values(by='Efectividad', ascending=False)
        else:
            st.warning("Columna 'Call_Center' no encontrada en datos de mensajería para gráfico de efectividad.")
            
        # --- Paso 3: Gestion en Sistema ---
        total_gestion_sistema = 0
        df_gestion_sistema = pd.DataFrame()
        if not df_conversaciones.empty and 'Numero_Telefono' in df_conversaciones.columns:
            telefonos_novedades = set(_normalize_telefonos(df_novedades.get('Telefono_Cliente', pd.Series(dtype=str))))
            telefonos_novedades.update(_normalize_telefonos(df_novedades.get('Celular_Cliente', pd.Series(dtype=str))))
            
            if not telefonos_novedades:
                st.warning("No se encontraron teléfonos en 'Detalle_Novedades' para cruzar.")
            else:
                df_conversaciones['Numero_Telefono_Norm'] = _normalize_telefonos(df_conversaciones['Numero_Telefono'])
                df_gestion_sistema = df_conversaciones[df_conversaciones['Numero_Telefono_Norm'].isin(telefonos_novedades)].copy()
                total_gestion_sistema = len(df_gestion_sistema)

        # --- Paso 4: Clientes con Pago ---
        total_clientes_pago = 0
        if not df_gestion_sistema.empty:
            cedulas_con_pago = set(df_cartera[df_cartera['Estado_Pago'] == 'PAGO']['Cedula_Cliente'].dropna().astype(str))
            
            if cedulas_con_pago:
                map_tel_a_cedula = {}
                df_novedades_map = df_novedades.dropna(subset=['Cedula_Cliente']).copy()
                
                if 'Telefono_Cliente' in df_novedades_map.columns:
                    df_novedades_map['Telefono_Cliente_Norm'] = _normalize_telefonos(df_novedades_map['Telefono_Cliente'])
                    map1 = df_novedades_map.set_index('Telefono_Cliente_Norm')['Cedula_Cliente'].astype(str).to_dict()
                    map_tel_a_cedula.update(map1)
                
                if 'Celular_Cliente' in df_novedades_map.columns:
                    df_novedades_map['Celular_Cliente_Norm'] = _normalize_telefonos(df_novedades_map['Celular_Cliente'])
                    map2 = df_novedades_map.set_index('Celular_Cliente_Norm')['Cedula_Cliente'].astype(str).to_dict()
                    map_tel_a_cedula.update(map2)

                if map_tel_a_cedula:
                    df_gestion_sistema['Cedula_Mapeada'] = df_gestion_sistema['Numero_Telefono_Norm'].map(map_tel_a_cedula)
                    total_clientes_pago = df_gestion_sistema['Cedula_Mapeada'].isin(cedulas_con_pago).sum()

        data_funnel = {
            'Etapa': ['Mensajes Entregados', 'Conversaciones', 'Gestion en Sistema', 'Clientes con Pago'],
            'Cantidad': [total_mensajes, total_conversaciones, total_gestion_sistema, total_clientes_pago]
        }
        df_funnel_mensajeria = pd.DataFrame(data_funnel)

    except Exception as e:
        st.error(f"Error al procesar el embudo de mensajería: {e}")
        return {"df_funnel_mensajeria": pd.DataFrame(), "df_efectividad_mensajeria": pd.DataFrame()}
    
    return {
        "df_funnel_mensajeria": df_funnel_mensajeria,
        "df_efectividad_mensajeria": df_efectividad_mensajeria
    }