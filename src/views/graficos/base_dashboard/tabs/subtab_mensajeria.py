import streamlit as st
import pandas as pd
from src.views.graficos.base_dashboard import charts_call_center 

def render(df_mensajeria, df_cartera_detalle, df_funnel_mensajeria, df_efectividad_mensajeria):
    """
    Renderiza el contenido del sub-tab "Mensajería Call Center".
    """
    st.subheader("Registros de Mensajería")

    # --- [MODIFICADO] Mostrar gráficos en columnas ---
    col_msg1, col_msg2 = st.columns(2)

    with col_msg1:
        st.markdown("##### Embudo de Gestión")
        if not df_funnel_mensajeria.empty:
            fig_funnel = charts_call_center.create_mensajeria_funnel_chart(df_funnel_mensajeria)
            if fig_funnel:
                st.plotly_chart(fig_funnel, use_container_width=True)
            else:
                st.info("No se pudieron generar datos para el embudo de mensajería.")
        else:
            st.info("No hay datos disponibles para el embudo de mensajería.")
    
    with col_msg2:
        st.markdown("##### Efectividad por Call Center")
        if not df_efectividad_mensajeria.empty:
            fig_efectividad_msg = charts_call_center.create_efectividad_mensajeria_chart(df_efectividad_mensajeria)
            if fig_efectividad_msg:
                st.plotly_chart(fig_efectividad_msg, use_container_width=True)
            else:
                st.info("No se pudieron generar datos para el gráfico de efectividad.")
        else:
            st.info("No hay datos disponibles para el gráfico de efectividad de mensajería.")
    # --- [FIN MODIFICADO] ---
    
    st.markdown("---")

    # --- Mostrar la tabla de detalle ---
    st.markdown("#### Detalle de Registros de Mensajería")
    if df_mensajeria.empty:
        st.warning("No se encontraron registros de mensajería para los filtros seleccionados.")
        return
        
    st.info(f"Mostrando {len(df_mensajeria)} registros de mensajes que coinciden con los filtros.")
    
    # Aquí puedes añadir filtros específicos para este tab
    
    st.dataframe(df_mensajeria, use_container_width=True)