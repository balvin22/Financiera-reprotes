# main.py
from datetime import date
import streamlit as st
import data_loader
import ui_components
import data_processing
import filtering

# Imports de servicios y tabs
from tabs import tab_metricas, tab_seguimientos, tab_resultados, tab_datos_detallados, tab_comercial, tab_call_center
import src.views.graficos.base_dashboard.charts_resultados as chart_resultados
from src.services.comercial.comercial_service import prepare_tab5_data
from src.services.call_centers.call_center_service import prepare_tab6_data

# Configuración de página
st.set_page_config(layout="wide", page_title="Dashboard Cartera", page_icon="📊")

def main():
    st.title("📊 Dashboard de Información de Cartera")

    # --- 1. LÓGICA DE CARGA INICIAL (Persistencia en disco) ---
    if "df_cartera" not in st.session_state:
        # Intentamos cargar Parquets existentes de la carpeta data_bin
        res_local = data_loader.load_from_local_disk()
        if res_local[0] is not None:
            st.session_state.df_cartera = res_local[0]
            st.session_state.df_novedades = res_local[1]
            st.session_state.df_llamadas = res_local[2]
            st.session_state.df_mensajeria = res_local[3]
            st.session_state.df_fnz = res_local[4]
            st.session_state.alerts = {'llamadas_error': None, 'mensajeria_error': None, 'fnz_error': None, 'novedades_error': None}
            st.session_state.data_initialized = True

    # --- 2. SIDEBAR PARA NUEVOS ARCHIVOS ---
    with st.sidebar:
        st.header("Actualización de Datos")
        uploaded_file = st.file_uploader("Cargar reporte Excel (.xlsx)", type=["xlsx"])
        
        if uploaded_file:
            if st.button("🚀 Procesar y Guardar en Disco"):
                with st.spinner("Procesando Excel pesado..."):
                    res = data_loader.load_and_process_data(uploaded_file)
                    if res[0] is not None:
                        st.session_state.df_cartera = res[0]
                        st.session_state.df_novedades = res[1]
                        st.session_state.df_llamadas = res[2]
                        st.session_state.df_mensajeria = res[3]
                        st.session_state.df_fnz = res[4]
                        st.session_state.alerts = res[5]
                        st.session_state.data_initialized = True
                        st.success("¡Datos guardados localmente!")
                        st.rerun()

    # --- 3. VALIDACIÓN DE SEGURIDAD (Blindaje contra NoneType) ---
    # Si después de todo lo anterior no hay nada en session_state, paramos la ejecución.
    if st.session_state.get("df_cartera") is None:
        st.info("👋 Bienvenida. Por favor, carga un archivo Excel en la barra lateral para comenzar.")
        st.image("https://img.freepik.com/free-vector/uploading-concept-illustration_114360-782.jpg", width=400)
        return # <--- ESTO ES LO QUE EVITA EL ERROR DE 'copy()'

    # --- 4. ASIGNACIÓN DE VARIABLES ---
    df_cartera = st.session_state.df_cartera
    df_novedades = st.session_state.df_novedades
    df_llamadas = st.session_state.df_llamadas
    df_mensajeria = st.session_state.df_mensajeria
    df_fnz = st.session_state.df_fnz
    alerts = st.session_state.alerts

    # --- 5. PROCESAMIENTO Y FILTRADO ---
    # Ahora add_call_center_column recibirá un DataFrame real, nunca un None
    df_cartera = filtering.add_call_center_column(df_cartera)
    
    filters = ui_components.sidebar_filters(df_cartera)
    
    (
        df_cartera_clasica,
        df_cartera_tab6,
        df_novedades_filtrada, 
        df_llamadas_filtrada,
        df_mensajeria_filtrada
    ) = filtering.apply_main_filters(
        df_cartera, df_novedades, df_llamadas, df_mensajeria, filters
    )
    
    # --- 6. PREPARACIÓN DE DATA PARA TABS ---
    with st.spinner("Actualizando visualizaciones..."):
        tab1_data = data_processing.prepare_tab1_data(df_cartera_clasica)
        tab2_data = data_processing.prepare_tab2_data(df_cartera_clasica, df_novedades_filtrada)
        tab3_data = data_processing.prepare_tab3_data(df_cartera_clasica)
        tab4_data = data_processing.prepare_tab4_data(df_cartera_clasica, df_novedades_filtrada)
        tab5_data = prepare_tab5_data(df_cartera_clasica, df_fnz)
        tab6_data = prepare_tab6_data(
            df_cartera_tab6, 
            df_novedades_filtrada, 
            df_llamadas_filtrada,
            df_mensajeria_filtrada
        )
    
    # --- 7. RENDERIZADO DE TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Métricas Principales", "🔄 Seguimientos", "🎯 Resultados",
        "📄 Datos Detallados", "🛍️ Comercial", "👩🏻‍💻 Call Centers"
    ])

    with tab1: tab_metricas.render(tab1_data)
    with tab2: tab_seguimientos.render(tab2_data)
    with tab3: tab_resultados.render(tab3_data)
    with tab4: tab_datos_detallados.render(tab4_data)
    with tab5: tab_comercial.render(tab5_data)
    with tab6: tab_call_center.render(tab6_data, chart_resultados, alerts)
        
if __name__ == "__main__":
    main()