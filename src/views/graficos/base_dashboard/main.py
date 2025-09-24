# main.py
import streamlit as st
import data_loader
import ui_components
import charts_metricas
import charts_rodamientos
import charts_resultados
from config import COLUMNAS_DEFECTO_CARTERA
from streamlit_plotly_events import plotly_events

def main():
    st.set_page_config(layout="wide")
    st.title("📊 Dashboard de Información de Cartera")

    # --- Carga de Archivo ---
    uploaded_file = st.sidebar.file_uploader(
        "Cargar tu reporte de cartera (.xlsx)", type=["xlsx"]
    )

    if not uploaded_file:
        st.info("Por favor, carga un archivo para comenzar.")
        return

    # 1. Cargar y procesar datos
    df_cartera, df_novedades = data_loader.load_and_process_data(uploaded_file)
    # st.dataframe(df_cartera.head()) 
    if df_cartera is None:
        return

    # 2. Mostrar filtros en la barra lateral
    filters = ui_components.sidebar_filters(df_cartera)

    # 3. Aplicar filtros a los datos
    # Esta lógica de filtrado se queda en el main ya que coordina los datos
    df_cartera_filtrada = df_cartera[
        df_cartera["Empresa"].isin(filters['empresa']) &
        df_cartera["Franja_Meta"].isin(filters['franjas']) &
        df_cartera["Regional_Cobro"].isin(filters['regional_cobro']) &
        df_cartera["Franja_Cartera"].isin(filters['franja_cartera']) 
        # ... & Añade las demás condiciones de los filtros ...
    ].copy()

    if filters['novedades'] == "Con Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] > 0]
    elif filters['novedades'] == "Sin Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] == 0]

    cedulas_filtradas = df_cartera_filtrada["Cedula_Cliente"].unique()
    df_novedades_filtrada = df_novedades[df_novedades["Cedula_Cliente"].isin(cedulas_filtradas)]

    # 4. Renderizar la página principal
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Métricas Principales",
        "🔄 Análisis de Rodamiento",
        "📄 Datos Detallados", 
        "🎯 Resultados"
    ])

    with tab1:
        st.header("Visualizaciones Generales")
        # Aquí irían las métricas principales (KPIs)
        
        col1, col2 = st.columns(2)
        with col1:
            fig_regional = charts_metricas.create_regional_bar_chart(df_cartera_filtrada)
            st.plotly_chart(fig_regional, use_container_width=True)
        
        with col2:
            fig_cobro = charts_metricas.create_cobro_bar_chart(df_cartera_filtrada)
            if fig_cobro:
                st.plotly_chart(fig_cobro, use_container_width=True)
            else:
                st.info("Faltan datos para el gráfico de Grupo de Cobro.")

        st.markdown("---") # Separador visual
       # --- Nueva fila para los dos gráficos de abajo ---
        col3, col4 = st.columns(2) # <--- Creamos 2 columnas nuevas aquí

        with col3: # <--- El gráfico de desembolso va en la primera columna
            fig_desembolso_ano = charts_metricas.create_desembolso_por_ano_chart(df_cartera_filtrada)
            if fig_desembolso_ano is not None:
                st.plotly_chart(fig_desembolso_ano, use_container_width=True)
            else:
                st.info("No se encontraron datos de desembolso entre 2018 y el año actual para los filtros seleccionados.")

        with col4: # <--- El nuevo gráfico de sol va en la segunda columna
            fig_vigencia_sunburst = charts_metricas.create_vigencia_sunburst_chart(df_cartera_filtrada)
            if fig_vigencia_sunburst:
                st.plotly_chart(fig_vigencia_sunburst, use_container_width=True)
            else:
                st.info("No hay datos de vigencia disponibles o la columna 'Fecha_Cuota_Vigente' no existe en los datos.")

    with tab2:
        st.header("Análisis de Rodamiento y Gestión")
        
        if 'recaudo_seleccionado' not in st.session_state:
            st.session_state.recaudo_seleccionado = "TODOS"
        if 'last_click_event' not in st.session_state:
            st.session_state.last_click_event = None

        # --- OPTIMIZACIÓN: Pre-cálculo de datos para los gráficos ---
        conteo_estados_donut = charts_rodamientos.prepare_donut_data(df_cartera_filtrada)
        grouped_sunburst, conteo_gestion_sunburst = charts_rodamientos.prepare_sunburst_data(df_cartera_filtrada, df_novedades_filtrada)

        # --- FILA SUPERIOR: Gráfico Principal Interactivo ---
        top_left, top_center, top_right = st.columns([0.5, 2, 0.5])
        with top_center:
            estado_actual = st.session_state.recaudo_seleccionado

            if st.button("Ver Todos"):
                st.session_state.recaudo_seleccionado = "TODOS"
                st.rerun() 
            
            # El gráfico se crea a partir de los datos cacheados
            donut_chart_fig = charts_rodamientos.create_recaudo_donut_chart(
                conteo_estados_donut, 
                estado_seleccionado=estado_actual
            )
            
            if donut_chart_fig:
                puntos_seleccionados = plotly_events(
                    donut_chart_fig, 
                    click_event=True, 
                    key=f"donut_selector_{estado_actual}"
                )
                if puntos_seleccionados:
                    if estado_actual == "TODOS":
                        clicked_index = puntos_seleccionados[0]['pointNumber']
                        labels_recaudo = ['PAGO', 'SIN PAGO']
                        st.session_state.recaudo_seleccionado = labels_recaudo[clicked_index]
                    else:
                        st.session_state.recaudo_seleccionado = "TODOS"
                    st.rerun()
            else:
                st.info("No hay datos de recaudo para mostrar.")
        
        st.markdown("---")

        # --- FILA INFERIOR: Gráficos de Detalle ---
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.subheader("Análisis de Gestión")
            # El gráfico se crea a partir de los datos cacheados
            sunburst_chart_fig = charts_rodamientos.create_gestion_sunburst_chart(
                grouped_sunburst, 
                conteo_gestion_sunburst
            )
            if sunburst_chart_fig:
                st.plotly_chart(sunburst_chart_fig, use_container_width=True)
            else:
                st.info("No hay datos de gestión para mostrar.")

        with col_der:
            st.subheader("Detalle por Selección")
            estado_actual_detalle = st.session_state.recaudo_seleccionado
            
            
            if estado_actual_detalle == "TODOS":
                df_cartera_detalle = df_cartera_filtrada
                df_novedades_detalle = df_novedades_filtrada
            elif estado_actual_detalle == 'PAGO':
                df_cartera_detalle = df_cartera_filtrada[df_cartera_filtrada['Total_Recaudo'] > 50000]
            else:
                df_cartera_detalle = df_cartera_filtrada[df_cartera_filtrada['Total_Recaudo'] <= 50000]

            cedulas_detalle = df_cartera_detalle['Cedula_Cliente'].unique()
            df_novedades_detalle_filtradas = df_novedades_filtrada[df_novedades_filtrada['Cedula_Cliente'].isin(cedulas_detalle)]

            # --- OPTIMIZACIÓN: Pre-cálculo para el gráfico de detalle ---
            grouped_detalle, conteo_gestion_detalle = charts_rodamientos.prepare_sunburst_data(df_cartera_detalle, df_novedades_detalle_filtradas)

            detalle_fig = charts_rodamientos.create_recaudo_detail_sunburst_chart(
                grouped_detalle,
                conteo_gestion_detalle,
                estado_actual_detalle
            )
            if detalle_fig:
                st.plotly_chart(detalle_fig, use_container_width=True)
            else:
                st.warning(f"No se encontraron datos de gestión para la selección '{estado_actual_detalle}'.")

        st.markdown("---") 

        st.subheader("Seguimineto")

        # 1. Obtenemos las opciones de 'Rodamiento' de los datos ya filtrados globalmente
        rodamiento_options = sorted(df_cartera_filtrada['Rodamiento'].unique())

        # 2. Creamos el widget multiselect para el filtro local
        # Este widget solo existirá aquí y no afectará a otros gráficos
        selected_rodamientos = st.multiselect(
            "Selecciona los estados de Rodamiento a visualizar:",
            options=rodamiento_options,
            default=rodamiento_options # Por defecto, mostramos todos
        )

        # 3. Creamos un nuevo DataFrame aplicando este filtro local
        df_rodamiento_filtrada_localmente = df_cartera_filtrada[df_cartera_filtrada['Rodamiento'].isin(selected_rodamientos)]

        # 4. Pasamos el DataFrame filtrado localmente a la función del gráfico
        fig_rodamiento = charts_rodamientos.create_rodamiento_bar_chart(df_rodamiento_filtrada_localmente)
        
        if fig_rodamiento:
            st.plotly_chart(fig_rodamiento, use_container_width=True)
        else:
            st.info("Selecciona al menos un estado de Rodamiento para ver el gráfico.")
        

    with tab3:
        st.header("Explorador de Datos")
        ui_components.display_detailed_data(df_cartera_filtrada, "Cartera Filtrada", COLUMNAS_DEFECTO_CARTERA)
        st.markdown("---")

        # --- CÓDIGO MEJORADO ---
        if not df_novedades_filtrada.empty:
            ui_components.display_detailed_data(
                df_novedades_filtrada, 
                "Novedades Filtradas", 
                df_novedades_filtrada.columns.tolist()
            )
        else:
            st.warning("No se encontraron novedades que coincidan con los filtros de cartera seleccionados.")

    # with tab4:
    #     st.header("Resultados de Cumplimiento por Zona y Franja")

    #     # --- CORRECCIÓN FINAL ---
    #     # Llamamos a la función de preparación pasando el DataFrame ORIGINAL
    #     # y los filtros de la barra lateral como argumentos.
    #     df_resultados = charts_resultados.prepare_resultados_data(
    #         df_cartera, # Pasamos el DataFrame original, sin filtrar
    #         filters['empresa'],
    #         filters['regional_cobro']
    #     )

    #     if df_resultados.empty:
    #         st.warning("No se encontraron datos para las franjas '1 A 30' a '181 A 360' con los filtros seleccionados.")
    #     else:
    #         zonas_disponibles = sorted(df_resultados['Zona'].unique())
            
    #         zona_seleccionada = st.selectbox(
    #             "Selecciona la Zona para todos los resultados:",
    #             options=zonas_disponibles,
    #             key="zona_selector_global_resultados" 
    #         )

    #         st.markdown("---")
            
    #         datos_zona = df_resultados[df_resultados['Zona'] == zona_seleccionada]

    #         franjas_a_mostrar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
    #         cols = st.columns(4)
            
    #         for col, franja in zip(cols, franjas_a_mostrar):
    #             with col:
    #                 st.subheader(f"Franja: {franja}")
    #                 data_row = datos_zona[datos_zona['Franja_Meta'] == franja]
                    
    #                 if not data_row.empty:
    #                     meta = data_row['Meta_Total'].iloc[0]
    #                     recaudo = data_row['Recaudo_Total'].iloc[0]
    #                     cumplimiento = data_row['Cumplimiento_%'].iloc[0]
                        
    #                     fig_gauge = charts_resultados.create_gauge_chart(
    #                         value=cumplimiento, meta=meta, recaudo=recaudo, title=zona_seleccionada
    #                     )
    #                     st.plotly_chart(fig_gauge, use_container_width=True)
    #                 else:
    #                     st.warning(f"Sin datos para esta franja.")


if __name__ == "__main__":
    main()