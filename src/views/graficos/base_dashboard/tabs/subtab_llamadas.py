import streamlit as st
import pandas as pd
from src.views.graficos.base_dashboard import charts_call_center

def render(llamadas_stats, df_grafico_llamadas, df_llamadas_filtradas, df_efectividad_call, df_llamadas_por_dia, alerta_umbral):
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
    
    st.markdown("#### Tendencia de Llamadas Diarias (Días Hábiles)")
    opciones_filtro = ['CON RESPUESTA', 'SIN RESPUESTA']
    
    # 1. Crear el filtro Popover
    with st.popover("Filtrar por tipo de respuesta...", use_container_width=True):
        if st.button("Todas", use_container_width=True, key="select_all_tendencia_llamadas"):
            for opt in opciones_filtro: st.session_state[f"tendencia_call_{opt}"] = True
        if st.button("Ninguna", use_container_width=True, key="deselect_all_tendencia_llamadas"):
            for opt in opciones_filtro: st.session_state[f"tendencia_call_{opt}"] = False
        st.markdown("---")
        
        for opt in opciones_filtro:
            # Por defecto, todo está seleccionado (True) para cargar "TODAS"
            if f"tendencia_call_{opt}" not in st.session_state: 
                st.session_state[f"tendencia_call_{opt}"] = True
            st.checkbox(opt, key=f"tendencia_call_{opt}")
            
    # 2. Recolectar las selecciones
    selected_filtros = [opt for opt in opciones_filtro if st.session_state.get(f"tendencia_call_{opt}", True)]
    
    # 3. Mostrar un resumen de la selección
    if len(selected_filtros) == len(opciones_filtro):
        st.caption("Mostrando: TODAS")
    elif not selected_filtros:
        st.caption("Mostrando: NINGUNA")
    else:
        st.caption(f"Mostrando: {', '.join(selected_filtros)}")

    # 4. Generar y mostrar el gráfico (pasando el umbral)
    if not df_llamadas_por_dia.empty:
        fig_area_llamadas = charts_call_center.create_llamadas_por_dia_area_chart(
            df_llamadas_dia=df_llamadas_por_dia,
            filtros_respuesta=selected_filtros,
            alerta_umbral=alerta_umbral # Pasa el umbral al gráfico
        )
        if fig_area_llamadas:
            st.plotly_chart(fig_area_llamadas, use_container_width=True)
    else:
        st.info("No hay datos disponibles para generar el gráfico de tendencia de llamadas.")
    
    st.markdown("---")
    