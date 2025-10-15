import streamlit as st
import charts_metricas

def render(tab1_data):
    """
    Renderiza el contenido de la pestaña "Métricas Principales".
    """
    st.header("Visualizaciones Generales")
    col1, col2 = st.columns(2)

    with col1:
        # <-- CAMBIO: Usamos los datos pre-procesados del diccionario
        df_agg_regional = tab1_data.get("regional")
        if df_agg_regional is not None and not df_agg_regional.empty:
            fig_regional = charts_metricas.create_regional_bar_chart(df_agg_regional)
            st.plotly_chart(fig_regional, use_container_width=True)
        else:
            st.info("No hay datos para el gráfico de Regional.")

    with col2:
        # <-- CAMBIO: Usamos los datos pre-procesados del diccionario
        df_agg_cobro = tab1_data.get("cobro")
        if df_agg_cobro is not None:
            fig_cobro = charts_metricas.create_cobro_bar_chart(df_agg_cobro)
            st.plotly_chart(fig_cobro, use_container_width=True)
        else:
            st.info("Faltan datos para el gráfico de Grupo de Cobro.")

    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        # <-- CAMBIO: Usamos los datos pre-procesados del diccionario
        df_agg_desembolso = tab1_data.get("desembolso")
        if df_agg_desembolso is not None:
            fig_desembolso_ano = charts_metricas.create_desembolso_por_ano_chart(df_agg_desembolso)
            st.plotly_chart(fig_desembolso_ano, use_container_width=True)
        else:
            st.info("No se encontraron datos de desembolso para los filtros seleccionados.")

    with col4:
        # <-- CAMBIO: Usamos los datos pre-procesados del diccionario
        df_agg_vigencia = tab1_data.get("vigencia")
        if df_agg_vigencia is not None and not df_agg_vigencia.empty:
            fig_vigencia_sunburst = charts_metricas.create_vigencia_sunburst_chart(df_agg_vigencia)
            st.plotly_chart(fig_vigencia_sunburst, use_container_width=True)
        else:
            st.info("No hay datos de vigencia disponibles.")
