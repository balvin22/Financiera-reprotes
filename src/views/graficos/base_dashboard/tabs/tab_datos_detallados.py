# tab_datos_detallados.py
import streamlit as st
import pandas as pd
import io 
import ui_components
from config import COLUMNAS_DEFECTO_CARTERA

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
        worksheet = writer.sheets['Datos']
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, len(str(col)) + 5)
    return output.getvalue()

def render(tab4_data):
    st.header("Explorador de Datos")

    # ---------------- SECCIÓN CARTERA ----------------
    df_cartera_para_mostrar = tab4_data["cartera_para_mostrar"]
    
    # 1. Llamamos a la función y CAPTURAMOS lo que retorna (el df con columnas filtradas)
    df_visible_cartera = ui_components.display_detailed_data(
        df_cartera_para_mostrar, 
        "Cartera Filtrada", 
        COLUMNAS_DEFECTO_CARTERA
    )

    # 2. El botón de descarga usa 'df_visible_cartera' en vez del original
    if df_visible_cartera is not None and not df_visible_cartera.empty:
        excel_cartera = convert_df_to_excel(df_visible_cartera)
        st.download_button(
            label="📥 Descargar Cartera (Vista Actual)",
            data=excel_cartera,
            file_name='reporte_cartera_filtrado.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='btn_descarga_cartera'
        )

    st.markdown("---")

    # ---------------- SECCIÓN NOVEDADES ----------------
    df_novedades_para_mostrar = tab4_data["novedades_para_mostrar"]
    
    if not df_novedades_para_mostrar.empty:
        # 1. Capturamos el retorno también aquí
        df_visible_novedades = ui_components.display_detailed_data(
            df_novedades_para_mostrar, 
            "Novedades Filtradas", 
            df_novedades_para_mostrar.columns.tolist()
        )

        # 2. Descargamos 'df_visible_novedades'
        if df_visible_novedades is not None and not df_visible_novedades.empty:
            excel_novedades = convert_df_to_excel(df_visible_novedades)
            st.download_button(
                label="📥 Descargar Novedades (Vista Actual)",
                data=excel_novedades,
                file_name='reporte_novedades_filtrado.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                key='btn_descarga_novedades'
            )
    else:
        st.warning("No se encontraron novedades que coincidan con los filtros.")