import streamlit as st
import pandas as pd
from src.views.graficos.base_dashboard import charts_call_center # Lo importamos para futuros gráficos

# --- [MODIFICADO] La firma de la función ahora acepta los dos argumentos ---
def render(df_mensajeria, df_cartera_detalle):
    """
    Renderiza el contenido del sub-tab "Mensajería Call Center".
    """
    st.subheader("Análisis de Registros de Mensajería")

    # --- [NUEVO] Usamos df_mensajeria para la validación ---
    if df_mensajeria.empty:
        st.warning("No se encontraron registros de mensajería para los filtros seleccionados.")
        return

    st.info(f"Mostrando {len(df_mensajeria)} registros de mensajes que coinciden con los filtros.")
    
    # --- Aquí puedes añadir filtros específicos para este tab ---
    # Por ejemplo, filtrar por 'Estado_Menasaje'
    
    st.dataframe(df_mensajeria, use_container_width=True)
    
    st.markdown("---")

    # --- Aquí irán tus gráficos ---
    st.subheader("Gráficos de Mensajería")
    st.info("Próximamente: Gráficos de mensajería.")
    
    # Ejemplo de cómo llamarías a un gráfico (cuando lo crees):
    # fig = charts_call_center.create_grafico_mensajes_estado(df_mensajeria)
    # st.plotly_chart(fig, use_container_width=True)

