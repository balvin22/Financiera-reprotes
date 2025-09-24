# main.py
import streamlit as st
import data_loader
import ui_components
import charts_metricas
import charts_rodamientos
import charts_resultados
import data_processing
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
    
     # --- CAMBIO CLAVE: Procesamiento centralizado ---
    # Llamamos a nuestra nueva función UNA SOLA VEZ para preparar todos los datos del tab 1.
    # Gracias al caché, esto será instantáneo en la mayoría de las interacciones.
    tab1_data = data_processing.prepare_tab1_data(df_cartera_filtrada)
    tab2_data = data_processing.prepare_tab2_data(df_cartera_filtrada, df_novedades_filtrada)


    # 4. Renderizar la página principal
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Métricas Principales",
        "🔄 Análisis de Rodamiento",
        "📄 Datos Detallados", 
        "🎯 Resultados"
    ])

    with tab1:
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
                
                
    with tab2:
        st.header("Análisis de Rodamiento y Gestión")

        # --- Inicialización del estado de la sesión ---
        if 'recaudo_seleccionado' not in st.session_state:
            st.session_state.recaudo_seleccionado = "TODOS"

        conteo_estados_donut = tab2_data.get("donut_data")
            
        top_left, top_center, top_right = st.columns([0.5, 2, 0.5])
        
        with top_center:
            estado_actual = st.session_state.recaudo_seleccionado

        # Botón para resetear la selección
            if st.button("Ver Todos"):
                st.session_state.recaudo_seleccionado = "TODOS"

            # Creación del gráfico de dona
            donut_chart_fig = charts_rodamientos.create_recaudo_donut_chart(
                conteo_estados_donut,
                estado_seleccionado=estado_actual
            )

            if donut_chart_fig:
                # Usamos plotly_events, que está diseñado para este tipo de clic
                puntos_seleccionados = plotly_events(
                    donut_chart_fig,
                    click_event=True,
                    key="donut_chart_events" # Key estática para no reconstruir el gráfico
                )

                # La información se devuelve como una lista, no se guarda en session_state
                if puntos_seleccionados:
                    # Obtenemos la etiqueta del punto presionado del diccionario que devuelve la librería
                    clicked_label = puntos_seleccionados[0]["label"]

                    if estado_actual == "TODOS":
                        st.session_state.recaudo_seleccionado = clicked_label
                    else:
                        st.session_state.recaudo_seleccionado = "TODOS"
                    
                    # Forzamos un rerun suave para actualizar la vista
                    st.rerun()
            else:
                st.info("No hay datos de recaudo para mostrar.")
                st.markdown("---")

        # --- FILA INFERIOR: Gráficos de Detalle ---
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.subheader("Análisis de Gestión")
            grouped_sunburst = tab2_data.get("sunburst_initial_grouped")
            conteo_gestion_sunburst = tab2_data.get("sunburst_initial_counts")
            
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
            
            # --- CAMBIO CRÍTICO: Se usa la búsqueda directa de datos pre-calculados ---
            if estado_actual_detalle == 'PAGO':
                grouped_detalle, conteo_gestion_detalle = tab2_data.get("detalle_pago", (None, None))
            elif estado_actual_detalle == 'SIN PAGO':
                grouped_detalle, conteo_gestion_detalle = tab2_data.get("detalle_sin_pago", (None, None))
            else: # "TODOS"
                grouped_detalle = tab2_data.get("sunburst_initial_grouped")
                conteo_gestion_detalle = tab2_data.get("sunburst_initial_counts")
            
            detalle_fig = charts_rodamientos.create_recaudo_detail_sunburst_chart(
                grouped_detalle,
                conteo_gestion_detalle,
                estado_actual_detalle
            )
            if detalle_fig:
                st.plotly_chart(detalle_fig, use_container_width=True)
            else:
                st.warning(f"No se encontraron datos de gestión para la selección.")

        st.markdown("---") 
        st.subheader("Seguimiento")

        # 1. Obtenemos los datos ya agregados
        agg_rodamiento = tab2_data.get("rodamiento_data")
        if agg_rodamiento is not None and not agg_rodamiento.empty:
            rodamiento_options = sorted(agg_rodamiento['Rodamiento'].unique())
            
            # 2. Creamos el widget multiselect
            selected_rodamientos = st.multiselect(
                "Selecciona los estados de Rodamiento a visualizar:",
                options=rodamiento_options,
                default=rodamiento_options
            )
            
            # 3. Filtramos el DataFrame PEQUEÑO y agregado (instantáneo)
            agg_rodamiento_filtrado = agg_rodamiento[agg_rodamiento['Rodamiento'].isin(selected_rodamientos)]
            
            # 4. Pasamos los datos ya filtrados y agregados al gráfico
            fig_rodamiento = charts_rodamientos.create_rodamiento_bar_chart(agg_rodamiento_filtrado)
            
            if fig_rodamiento:
                st.plotly_chart(fig_rodamiento, use_container_width=True)
            else:
                st.info("Selecciona al menos un estado de Rodamiento para ver el gráfico.")
        else:
            st.info("No hay datos de Rodamiento disponibles para los filtros seleccionados.")

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

    with tab4:
        st.header("Resultados de Cumplimiento por Zona y Franja")

        # --- CORRECCIÓN FINAL ---
        # Llamamos a la función de preparación pasando el DataFrame ORIGINAL
        # y los filtros de la barra lateral como argumentos.
        df_resultados = charts_resultados.prepare_resultados_data(
            df_cartera, # Pasamos el DataFrame original, sin filtrar
            filters['empresa'],
            filters['regional_cobro']
        )

        if df_resultados.empty:
            st.warning("No se encontraron datos para las franjas '1 A 30' a '181 A 360' con los filtros seleccionados.")
        else:
            zonas_disponibles = sorted(df_resultados['Zona'].unique())
            
            zona_seleccionada = st.selectbox(
                "Selecciona la Zona para todos los resultados:",
                options=zonas_disponibles,
                key="zona_selector_global_resultados" 
            )

            st.markdown("---")
            
            datos_zona = df_resultados[df_resultados['Zona'] == zona_seleccionada]

            franjas_a_mostrar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
            cols = st.columns(4)
            
            for col, franja in zip(cols, franjas_a_mostrar):
                with col:
                    st.subheader(f"Franja: {franja}")
                    data_row = datos_zona[datos_zona['Franja_Meta'] == franja]
                    
                    if not data_row.empty:
                        meta = data_row['Meta_Total'].iloc[0]
                        recaudo = data_row['Recaudo_Total'].iloc[0]
                        cumplimiento = data_row['Cumplimiento_%'].iloc[0]
                        
                        fig_gauge = charts_resultados.create_gauge_chart(
                            value=cumplimiento, meta=meta, recaudo=recaudo, title=zona_seleccionada
                        )
                        st.plotly_chart(fig_gauge, use_container_width=True)
                    else:
                        st.warning(f"Sin datos para esta franja.")


if __name__ == "__main__":
    main()