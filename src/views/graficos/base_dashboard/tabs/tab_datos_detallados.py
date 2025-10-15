import streamlit as st 
import ui_components
from config import COLUMNAS_DEFECTO_CARTERA


def render (tab4_data):
    st.header("Explorador de Datos")

    # Usamos el dataframe del diccionario devuelto por la función
    df_cartera_para_mostrar = tab4_data["cartera_para_mostrar"]
    ui_components.display_detailed_data(
        df_cartera_para_mostrar, 
        "Cartera Filtrada", 
        COLUMNAS_DEFECTO_CARTERA
    )
    st.markdown("---")

    # Hacemos lo mismo para las novedades
    df_novedades_para_mostrar = tab4_data["novedades_para_mostrar"]
    if not df_novedades_para_mostrar.empty:
        ui_components.display_detailed_data(
            df_novedades_para_mostrar, 
            "Novedades Filtradas", 
            df_novedades_para_mostrar.columns.tolist()
        )
    else:
        st.warning("No se encontraron novedades que coincidan con los filtros de cartera seleccionados.")