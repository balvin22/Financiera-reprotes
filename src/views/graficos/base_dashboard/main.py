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

    # --- 1. LÓGICA DE CARGA INICIAL (Persistencia en disco con Parquet) ---
    if "data_initialized" not in st.session_state:
        # Intentamos cargar Parquets existentes usando la nueva lógica del tempfile
        res_local = data_loader.load_from_local_disk()
        
        # Validamos si res_local[0] no es None Y no está vacío
        if res_local[0] is not None and not res_local[0].empty:
            st.session_state.df_cartera = res_local[0]
            st.session_state.df_novedades = res_local[1]
            st.session_state.df_llamadas = res_local[2]
            st.session_state.df_mensajeria = res_local[3]
            st.session_state.df_fnz = res_local[4]
            st.session_state.alerts = {'llamadas_error': None, 'mensajeria_error': None, 'fnz_error': None, 'novedades_error': None}
            st.session_state.data_initialized = True
        else:
            # Si no hay parquets, inicializamos en False
            st.session_state.data_initialized = False

    # --- 2. SIDEBAR PARA NUEVOS ARCHIVOS ---
    with st.sidebar:
        st.header("Actualización de Datos")
        uploaded_file = st.file_uploader("Cargar reporte Excel (.xlsx)", type=["xlsx"])
        
        if uploaded_file:
            if st.button("🚀 Procesar y Guardar en Disco"):
                with st.spinner("Procesando Excel pesado (esto tomará un momento)..."):
                    # Esta función ahora guarda los Parquet en el temp folder
                    res = data_loader.load_and_process_data(uploaded_file)
                    if res[0] is not None:
                        st.session_state.df_cartera = res[0]
                        st.session_state.df_novedades = res[1]
                        st.session_state.df_llamadas = res[2]
                        st.session_state.df_mensajeria = res[3]
                        st.session_state.df_fnz = res[4]
                        st.session_state.alerts = res[5]
                        st.session_state.data_initialized = True
                        st.success("¡Datos guardados localmente! Procesamiento rápido activado.")
                        st.rerun()

    # --- 3. VALIDACIÓN DE SEGURIDAD ---
    if not st.session_state.get("data_initialized", False):
        st.info("👋 Bienvenida. Por favor, carga un archivo Excel en la barra lateral para comenzar.")
        # Quitamos la imagen externa temporalmente para evitar bloqueos de red en desktop apps
        st.markdown("### 📊 Sube tu archivo `.xlsx` para generar el panel interactivo.")
        return 

    # --- 4. ASIGNACIÓN DE VARIABLES LIGERAS (Desde Parquet) ---
    df_cartera = st.session_state.df_cartera
    df_novedades = st.session_state.df_novedades
    df_llamadas = st.session_state.df_llamadas
    df_mensajeria = st.session_state.df_mensajeria
    df_fnz = st.session_state.df_fnz
    alerts = st.session_state.alerts

    # --- 5. FILTRADO GLOBAL ---
    # Como df_cartera ahora viene de Parquet (optimizado en memoria), esto será muy rápido
    df_cartera = filtering.add_call_center_column(df_cartera)
    
    # Extraemos los filtros seleccionados por el usuario
    filters = ui_components.sidebar_filters(df_cartera)
    
    # Aplicamos los filtros a los DataFrames base
    (
        df_cartera_clasica,
        df_cartera_tab6,
        df_novedades_filtrada, 
        df_llamadas_filtrada,
        df_mensajeria_filtrada
    ) = filtering.apply_main_filters(
        df_cartera, df_novedades, df_llamadas, df_mensajeria, filters
    )
    
    # --- 6. RENDERIZADO Y CÁLCULO PEREZOSO (LAZY RENDERING) ---
    # Creamos las pestañas PRIMERO
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Métricas Principales", "🔄 Seguimientos", "🎯 Resultados",
        "📄 Datos Detallados", "🛍️ Comercial", "👩🏻‍💻 Call Centers"
    ])

    # Envolvemos la preparación y el renderizado dentro de cada "with tab"
    # IMPORTANTE: Streamlit NO ejecuta lo que está dentro de un 'with tab' 
    # si el usuario no tiene esa pestaña abierta (a partir de versiones recientes).
    
    with tab1: 
        # Solo calcula si la pestaña está activa
        tab1_data = data_processing.prepare_tab1_data(df_cartera_clasica)
        tab_metricas.render(tab1_data)
        
    with tab2: 
        tab2_data = data_processing.prepare_tab2_data(df_cartera_clasica, df_novedades_filtrada)
        tab_seguimientos.render(tab2_data)
        
    with tab3: 
        tab3_data = data_processing.prepare_tab3_data(df_cartera_clasica)
        tab_resultados.render(tab3_data)
        
    with tab4: 
        tab4_data = data_processing.prepare_tab4_data(df_cartera_clasica, df_novedades_filtrada)
        tab_datos_detallados.render(tab4_data)
        
    with tab5: 
        tab5_data = prepare_tab5_data(df_cartera_clasica, df_fnz)
        tab_comercial.render(tab5_data)
        
    with tab6: 
        tab6_data = prepare_tab6_data(
            df_cartera_tab6, 
            df_novedades_filtrada, 
            df_llamadas_filtrada,
            df_mensajeria_filtrada
        )
        tab_call_center.render(tab6_data, chart_resultados, alerts)
        
if __name__ == "__main__":
    main()