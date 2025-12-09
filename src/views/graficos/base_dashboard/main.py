# main.py
from datetime import date
import streamlit as st
import data_loader
import ui_components
from tabs import tab_metricas, tab_seguimientos, tab_resultados, tab_datos_detallados, tab_comercial,tab_call_center
import src.views.graficos.base_dashboard.charts_resultados as chart_resultados
import data_processing
from src.services.comercial.comercial_service import prepare_tab5_data
from src.services.call_centers.call_center_service import prepare_tab6_data
import filtering

st.set_page_config(layout="wide")


def main():
    st.title("📊 Dashboard de Información de Cartera")
    uploaded_file = st.sidebar.file_uploader(
        "Cargar tu reporte de cartera (.xlsx)", type=["xlsx"]
    )
    if not uploaded_file:
        st.info("Por favor, carga un archivo para comenzar.")
        return
    
    # MODIFICACIÓN 1: Ahora load_and_process_data devuelve 5 valores, incluido 'alerts'
    df_cartera, df_novedades, df_llamadas, df_mensajeria,df_fnz, alerts = data_loader.load_and_process_data(uploaded_file) 
    
    if df_cartera is None:
        # Si df_cartera es None, el error crítico se muestra en data_loader.
        return
    
    df_cartera = filtering.add_call_center_column(df_cartera)
    filters = ui_components.sidebar_filters(df_cartera)
    df_cartera_filtrada, df_novedades_filtrada, df_llamadas_filtrada, df_mensajeria_filtrada = filtering.apply_main_filters(
        df_cartera, df_novedades, df_llamadas, df_mensajeria, filters
    )
    tab1_data = data_processing.prepare_tab1_data(df_cartera_filtrada)
    tab2_data = data_processing.prepare_tab2_data(df_cartera_filtrada, df_novedades_filtrada)
    tab3_data = data_processing.prepare_tab3_data(df_cartera_filtrada)
    tab4_data = data_processing.prepare_tab4_data(df_cartera_filtrada, df_novedades_filtrada)
    tab5_data = data_processing.prepare_tab5_data(df_cartera_filtrada)
    
    tab5_data = prepare_tab5_data(
        df_cartera_filtrada)
    
    tab6_data = prepare_tab6_data(
        df_cartera_filtrada, 
        df_novedades_filtrada,                                                                                                                                           
        df_llamadas_filtrada,
        df_mensajeria_filtrada
    )
    
    # 4. Renderizar la página principal
    tab1, tab2, tab3, tab4,tab5,tab6  = st.tabs([
        "📈 Métricas Principales",
        "🔄 Seguimientos",
        "🎯 Resultados",
        "📄 Datos Detallados", 
        "🛍️ Comercial",
        "👩🏻‍💻 Call Centers"
    ])

    with tab1:
        tab_metricas.render(tab1_data)
                        
    with tab2:
        tab_seguimientos.render(tab2_data)

    with tab3:
        tab_resultados.render(tab3_data)

    with tab4:
        tab_datos_detallados.render(tab4_data)

    with tab5:
        tab_comercial.render(tab5_data)
        
    with tab6:
        # MODIFICACIÓN 2: Pasar el diccionario de alertas al renderizador de la pestaña 6
        tab_call_center.render(tab6_data, chart_resultados, alerts)    
        
if __name__ == "__main__":
    main()