# main.py
from datetime import date
import streamlit as st
import data_loader
import ui_components
from tabs import tab_metricas, tab_seguimientos, tab_resultados, tab_datos_detallados, tab_comercial, tab_call_center
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
    
    # 1. Cargar
    df_cartera, df_novedades, df_llamadas, df_mensajeria, df_fnz, alerts = data_loader.load_and_process_data(uploaded_file) 
    
    if df_cartera is None:
        return
    
    # 2. Agregar columna (Lógica antigua)
    df_cartera = filtering.add_call_center_column(df_cartera)
    
    # 3. Filtros UI
    filters = ui_components.sidebar_filters(df_cartera)
    
    # 4. Aplicar Filtros (RECIBIMOS 2 CARTERAS DIFERENTES)
    (
        df_cartera_clasica,      # Data filtrada antigua (Para no dañar Tabs 1-5)
        df_cartera_tab6,         # Data filtrada nueva (Para sumar todo en Tab 6)
        df_novedades_filtrada, 
        df_llamadas_filtrada,
        df_mensajeria_filtrada
    ) = filtering.apply_main_filters(
        df_cartera, df_novedades, df_llamadas, df_mensajeria, filters
    )
    
    # 5. Distribuir la data

    # --- TABS 1 a 5: Usan df_cartera_clasica ---
    # Así se verán idénticos a como estaban antes.
    tab1_data = data_processing.prepare_tab1_data(df_cartera_clasica)
    tab2_data = data_processing.prepare_tab2_data(df_cartera_clasica, df_novedades_filtrada)
    tab3_data = data_processing.prepare_tab3_data(df_cartera_clasica)
    tab4_data = data_processing.prepare_tab4_data(df_cartera_clasica, df_novedades_filtrada)
    
    tab5_data = prepare_tab5_data(
        df_cartera_clasica, 
        df_fnz
    )
    
    # --- TAB 6: Usa df_cartera_tab6 ---
    # Aquí es donde verás la magia de la suma (114 + 34 = 148).
    tab6_data = prepare_tab6_data(
        df_cartera_tab6, 
        df_novedades_filtrada,                                                                                                                                           
        df_llamadas_filtrada,
        df_mensajeria_filtrada
    )
    
    # 6. Renderizar Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
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
        tab_call_center.render(tab6_data, chart_resultados, alerts)    
        
if __name__ == "__main__":
    main()