import streamlit as st
import pandas as pd
from src.views.graficos.base_dashboard import charts_call_center 

def render(df_novedades_mapeadas, df_agg_novedades_por_call, df_agg_novedades_por_tipo):
    """
    Renderiza el contenido del sub-tab "Novedades del Sistema".
    Muestra las novedades creadas en el sistema, asociadas al
    Call Center del agente que las creó.
    """
    st.subheader("Análisis de Novedades del Sistema por Call Center")

    if df_novedades_mapeadas.empty or df_agg_novedades_por_call.empty:
        st.info("No se encontraron datos de Novedades del Sistema o no se pudieron asociar a Call Centers.")
        return

    # --- Gráficos ---
    st.markdown("#### Total Novedades Creadas por Call Center")
    
    # Filtrar 'SIN ASIGNAR' para el gráfico principal si ocupa mucho
    df_grafico_call = df_agg_novedades_por_call[df_agg_novedades_por_call['Call_Center_Mapeado'] != 'SIN ASIGNAR']
    
    if not df_grafico_call.empty:
        # Aquí llamas al gráfico que debes crear en charts_call_center.py
        fig_total_call = charts_call_center.create_novedades_por_call_barchart(df_grafico_call)
        if fig_total_call:
            st.plotly_chart(fig_total_call, use_container_width=True)
        else:
            st.info("No se pudo generar el gráfico de novedades por call center.")
    else:
        st.info("No hay novedades asignadas a Call Centers para graficar.")

    st.markdown("---")
    
    st.markdown("#### Tipo de Novedades por Call Center")
    
    # Filtrar 'SIN ASIGNAR' para el gráfico principal
    df_grafico_tipo = df_agg_novedades_por_tipo[df_agg_novedades_por_tipo['Call_Center_Mapeado'] != 'SIN ASIGNAR']
    
    if not df_grafico_tipo.empty:
        # Llama al segundo gráfico que debes crear en charts_call_center.py
        fig_tipo_call = charts_call_center.create_novedades_por_tipo_stacked_barchart(df_grafico_tipo)
        if fig_tipo_call:
            st.plotly_chart(fig_tipo_call, use_container_width=True)
        else:
            st.info("No se pudo generar el gráfico de tipos de novedad por call center.")
    else:
        st.info("No hay tipos de novedades asignadas a Call Centers para graficar.")
        
    st.markdown("---")

    # --- Tabla de Detalle ---
    st.markdown("#### Detalle de Novedades Mapeadas")
    
    with st.expander("Mostrar/Ocultar tabla de detalle", expanded=False):
        # Opciones para la tabla
        columnas_mostrar = [
            'Call_Center_Mapeado',
            'Nombre_Usuario',
            'Tipo_Novedad',
            'Novedad',
            'Fecha_Novedad',
            'Cedula_Cliente'
        ]
        # Filtrar columnas que realmente existen en el DF
        columnas_disponibles = [col for col in columnas_mostrar if col in df_novedades_mapeadas.columns]
        
        if not columnas_disponibles:
            st.warning("No hay columnas de detalle para mostrar.")
            return

        st.dataframe(
            df_novedades_mapeadas[columnas_disponibles],
            use_container_width=True,
            hide_index=True
        )
        
        # Mostrar las que no se pudieron asignar
        df_sin_asignar = df_novedades_mapeadas[df_novedades_mapeadas['Call_Center_Mapeado'] == 'SIN ASIGNAR']
        st.info(f"Se encontraron {len(df_sin_asignar)} novedades que no se pudieron asignar a un Call Center.")
        if not df_sin_asignar.empty:
            st.write("Novedades 'SIN ASIGNAR':")
            st.dataframe(
                df_sin_asignar[columnas_disponibles],
                use_container_width=True,
                hide_index=True
            )