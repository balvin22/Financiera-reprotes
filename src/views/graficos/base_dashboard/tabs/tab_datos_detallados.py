# tab_datos_detallados.py
import streamlit as st
import pandas as pd
import io 
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
    st.header("Explorador de Datos Interactivo")
    st.markdown("<p style='color: #4B4B6A; font-size: 15px;'>👆 <b>Haz clic en cualquier fila</b> de la tabla principal para ver automáticamente su historial de novedades en la parte inferior.</p>", unsafe_allow_html=True)

    df_cartera = tab4_data["cartera_para_mostrar"]
    df_novedades = tab4_data["novedades_para_mostrar"]
    
    if df_cartera.empty:
        st.info("No hay datos de cartera para mostrar con los filtros actuales.")
        return

    # ---------------- 1. SELECCIÓN DE COLUMNAS ----------------
    col_header, col_count = st.columns([3, 1])
    with col_header:
        st.subheader("Cartera Filtrada")
    with col_count:
        st.markdown(f"<div style='text-align: right; padding-top: 10px; color: gray;'>Total: <b>{len(df_cartera):,}</b></div>", unsafe_allow_html=True)
    
    all_columns = df_cartera.columns.tolist()
    
    with st.expander("Personalizar columnas de: Cartera Filtrada", expanded=False):
        selected_columns = st.multiselect(
            "Selecciona las columnas visibles:",
            options=all_columns,
            default=[col for col in COLUMNAS_DEFECTO_CARTERA if col in all_columns],
            label_visibility="collapsed"
        )
    
    if not selected_columns:
        st.warning("⚠️ Por favor selecciona al menos una columna para visualizar la tabla.")
        return

    df_visible_cartera = df_cartera[selected_columns]

    # ---------------- 2. TABLA INTERACTIVA (CLICK A LA FILA) ----------------
    # El parámetro on_select="rerun" atrapa el clic del usuario
    evento_tabla = st.dataframe(
        df_visible_cartera,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row", # Solo permite seleccionar un crédito a la vez
        height=350
    )
    
    # Botón de descarga general (Descarga toda la tabla visualizada)
    excel_cartera = convert_df_to_excel(df_visible_cartera)
    st.download_button(
        label="📥 Descargar Cartera (Vista Actual)",
        data=excel_cartera,
        file_name='reporte_cartera_filtrado.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key='btn_descarga_cartera'
    )

    st.markdown("---")

    # ---------------- 3. LÓGICA DE DETALLE: DESPLIEGUE DE NOVEDADES ----------------
    filas_seleccionadas = evento_tabla.selection.rows
    
    if filas_seleccionadas:
        # Extraemos el índice de la fila que el usuario seleccionó
        indice_fila = filas_seleccionadas[0]
        
        # Vamos al DataFrame original y sacamos la Cédula y el Nombre usando ese índice
        cedula_seleccionada = df_cartera.iloc[indice_fila].get('Cedula_Cliente', None)
        nombre_seleccionado = df_cartera.iloc[indice_fila].get('Nombre_Cliente', 'Cliente Seleccionado')
        
        st.subheader(f"📋 Historial de Novedades")
        st.markdown(f"**Cliente:** {nombre_seleccionado} | **Cédula:** {cedula_seleccionada}")
        
        if cedula_seleccionada and not df_novedades.empty and 'Cedula_Cliente' in df_novedades.columns:
            # Filtramos las novedades SOLO para esa cédula
            df_novedades_cliente = df_novedades[df_novedades['Cedula_Cliente'] == cedula_seleccionada]
            
            if not df_novedades_cliente.empty:
                st.dataframe(
                    df_novedades_cliente, 
                    use_container_width=True, 
                    hide_index=True
                )
                
                # Botón de descarga exclusivo para este cliente
                excel_nov_cliente = convert_df_to_excel(df_novedades_cliente)
                st.download_button(
                    label=f"📥 Descargar Historial de {nombre_seleccionado}",
                    data=excel_nov_cliente,
                    file_name=f'novedades_{cedula_seleccionada}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    key='btn_descarga_nov_cliente'
                )
            else:
                st.info("Este crédito no tiene novedades o gestiones registradas.")
        else:
            st.info("No se encontró información de cédula para buscar novedades en este registro.")
            
    else:
        # Lo que se muestra cuando el usuario NO ha hecho clic en ninguna fila
        st.info("👆 Selecciona un crédito en la tabla de arriba para inspeccionar sus novedades.")
        
        # Mantenemos las novedades globales disponibles en un acordeón por si alguien las quiere descargar todas
        with st.expander("Ver o descargar TODAS las Novedades filtradas", expanded=False):
            if not df_novedades.empty:
                st.dataframe(df_novedades, use_container_width=True, hide_index=True, height=250)
                excel_nov_global = convert_df_to_excel(df_novedades)
                st.download_button(
                    label="📥 Descargar TODAS las novedades",
                    data=excel_nov_global,
                    file_name='todas_las_novedades_filtradas.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    key='btn_descarga_nov_global'
                )
            else:
                st.write("No hay novedades registradas con los filtros actuales.")