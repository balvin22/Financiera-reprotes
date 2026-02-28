import streamlit as st
import pandas as pd
from src.views.graficos.base_dashboard import charts_call_center

def render(llamadas_stats, df_grafico_llamadas, df_llamadas_filtradas, df_efectividad_call, df_llamadas_por_dia, alerta_umbral):
    st.subheader("Registros de Llamadas")
    if not llamadas_stats or llamadas_stats.get("total_llamadas", 0) == 0:
        st.warning("No se encontraron registros de llamadas para los Call Centers seleccionados.")
        return
        
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
    
    st.markdown("#### Tendencia de Llamadas Diarias (Días Hábiles)")
    
    # --- NUEVO DISEÑO ELEGANTE CON TOGGLES (INTERRUPTORES) ---
    st.markdown("<p style='font-size: 14px; color: #666; margin-bottom: 5px;'>Filtra las líneas de la gráfica:</p>", unsafe_allow_html=True)
    
    # Columnas estrechas para que queden bonitos y juntos
    col_t1, col_t2, _ = st.columns([1.5, 1.5, 7]) 
    
    with col_t1:
        mostrar_con = st.toggle("✅ Con Respuesta", value=True)
    with col_t2:
        mostrar_sin = st.toggle("❌ Sin Respuesta", value=True)
        
    # Armamos la lista de filtros según lo que esté encendido
    selected_filtros = []
    if mostrar_con: selected_filtros.append('CON RESPUESTA')
    if mostrar_sin: selected_filtros.append('SIN RESPUESTA')

    # Generar y mostrar el gráfico con doble línea
    if not df_llamadas_por_dia.empty:
        fig_area_llamadas = charts_call_center.create_llamadas_por_dia_area_chart(
            df_llamadas_dia=df_llamadas_por_dia,
            filtros_respuesta=selected_filtros,
            alerta_umbral=alerta_umbral 
        )
        if fig_area_llamadas:
            st.plotly_chart(fig_area_llamadas, use_container_width=True)
    else:
        st.info("No hay datos disponibles para generar el gráfico de tendencia de llamadas.")
    
    st.markdown("---")