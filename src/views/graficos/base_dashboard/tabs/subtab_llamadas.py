import streamlit as st
import pandas as pd
from src.views.graficos.base_dashboard import charts_call_center

def render(llamadas_stats, df_grafico_llamadas, df_llamadas_filtradas, df_efectividad_call):
    st.subheader("Registros de Llamadas")
    if not llamadas_stats or llamadas_stats.get("total_llamadas", 0) == 0:
        st.warning("No se encontraron registros de llamadas para los Call Centers seleccionados.")
        return
        
    st.markdown("#### Información de Llamadas")
    total_fmt = f'{llamadas_stats.get("total_llamadas", 0):,.0f}'.replace(',', '.')
    con_respuesta_fmt = f'{llamadas_stats.get("con_respuesta", 0):,.0f}'.replace(',', '.')
    sin_respuesta_fmt = f'{llamadas_stats.get("sin_respuesta", 0):,.0f}'.replace(',', '.')
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Llamadas", total_fmt)
    col2.metric("Con Respuesta", con_respuesta_fmt)
    col3.metric("Sin Respuesta", sin_respuesta_fmt)
    
    st.markdown("---")

    st.markdown("#### Efectividad de Llamadas")
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        fig_bar = charts_call_center.create_estado_llamadas_bar_chart(df_grafico_llamadas)
        if fig_bar:
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos para generar el gráfico de estado de llamadas.")

    with col_graf2:
        st.markdown("##### Efectividad por Call Center")
        fig_efectividad = charts_call_center.create_efectividad_call_chart(df_efectividad_call)
        if fig_efectividad:
            st.plotly_chart(fig_efectividad, use_container_width=True)
        else:
            st.info("No hay datos para generar el gráfico de efectividad.")
    st.markdown("---")
    
    st.markdown("#### Detalle de Registros de Llamadas")
    st.info(f"Mostrando {len(df_llamadas_filtradas)} registros de llamadas filtrados.")
    cols_detalle = [
        'Fecha_Llamada', 'Call_Center', 'Nombre_Call', 'Extension_Llamada', 
        'Destino_Llamada', 'Estado_Llamada', 'Duracion_Llamada', 'Grabacion_Llamada'
    ]
    # Filtramos solo las columnas que realmente existen
    cols_existentes = [col for col in cols_detalle if col in df_llamadas_filtradas.columns]
    st.dataframe(
        df_llamadas_filtradas[cols_existentes],
        use_container_width=True,
        hide_index=True
    )

