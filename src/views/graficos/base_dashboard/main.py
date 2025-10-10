# main.py
from datetime import date
import streamlit as st
import data_loader
import ui_components
import charts_metricas
import charts_rodamientos
import charts_resultados
import charts_retanqueos
import data_processing
from config import COLUMNAS_DEFECTO_CARTERA
import numpy as np

st.set_page_config(layout="wide")

def main():
    # st.set_page_config(layout="wide")
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
        # df_cartera["Franja_Meta"].isin(filters['franjas']) &
        df_cartera["Regional_Cobro"].isin(filters['regional_cobro']) &
        df_cartera["Franja_Cartera"].isin(filters['franja_cartera']) &
        df_cartera["Zona"].isin(filters['Zona'])
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
    df_resultados = data_processing.prepare_tab3_data(df_cartera_filtrada)


    # 4. Renderizar la página principal
    tab1, tab2, tab3, tab4,tab5 = st.tabs([
        "📈 Métricas Principales",
        "🔄 Seguimientos",
        "🎯 Resultados",
        "📄 Datos Detallados", 
        "🛍️ Comercial"
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
        st.header("Seguimientos y Gestión")
        col1, col2, col3 = st.columns([2, 1.2, 1.2])
        with col1:
            with st.container(border=True):
                st.markdown("<h5>Recaudo General</h5>", unsafe_allow_html=True)
                conteo_estados_donut = tab2_data.get("donut_data")
                donut_chart_fig = charts_rodamientos.create_recaudo_donut_chart(
                    conteo_estados_donut,
                    estado_seleccionado="TODOS",
                    show_center_text=False
                )
                if donut_chart_fig:
                    # Quitamos la altura fija para que se ajuste al contenedor
                    donut_chart_fig.update_layout(height=None, margin=dict(t=10, b=10))
                    st.plotly_chart(donut_chart_fig, use_container_width=True)
                else:
                    st.info("No hay datos de recaudo.")

        with col2:
            with st.container(border=True):
                st.markdown("<h5>Créditos con PAGO</h5>", unsafe_allow_html=True)
                grouped_data_pago, conteo_data_pago = tab2_data.get("detalle_pago", (None, None))
                sunburst_pago_fig = charts_rodamientos.create_nested_pie_chart(
                    grouped_data_pago,
                    conteo_data_pago,
                    height=250 # Una altura fija y más pequeña funciona bien aquí
                )
                if sunburst_pago_fig:
                    st.plotly_chart(sunburst_pago_fig, use_container_width=True)
                else:
                    st.info("No hay datos de gestión.")

        with col3:
            with st.container(border=True):
                st.markdown("<h5>Créditos SIN PAGO</h5>", unsafe_allow_html=True)
                grouped_data_sin_pago, conteo_data_sin_pago = tab2_data.get("detalle_sin_pago", (None, None))
                detalle_sin_pago_fig = charts_rodamientos.create_nested_pie_chart(
                    grouped_data_sin_pago,
                    conteo_data_sin_pago,
                    height=250 # La misma altura que el anterior para alinear
                )
                if detalle_sin_pago_fig:
                    st.plotly_chart(detalle_sin_pago_fig, use_container_width=True)
                else:
                    st.warning("No hay datos de gestión.")

        # --- El resto de tus componentes del tab2 continúan aquí abajo ---
        st.markdown("---")

        # El gráfico de "Todos los Créditos" puede ir abajo, ocupando todo el ancho
        st.markdown("<h5>Detalle de Gestión (Todos los Créditos)</h5>", unsafe_allow_html=True)
        with st.container(border=True): # Opcional: También puedes poner este en una tarjeta
            grouped_data_todos = tab2_data.get("sunburst_initial_grouped")
            conteo_data_todos = tab2_data.get("sunburst_initial_counts")
            sunburst_todos_fig = charts_rodamientos.create_nested_pie_chart(
                grouped_data_todos,
                conteo_data_todos,
                height=450
            )
            if sunburst_todos_fig:
                st.plotly_chart(sunburst_todos_fig, use_container_width=True)
            else:
                st.info("No hay datos de gestión para mostrar.")
        st.markdown("---")

        st.header("Análisis y Búsqueda Detallada de Créditos")
        # 1. Obtenemos el dataframe completo con toda la información
        df_completo = tab2_data.get("data_para_tabla")

        if df_completo is not None and not df_completo.empty:
            st.write("#### Filtros de Búsqueda")
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                filtro_pago = st.selectbox(
                    "Estado de Pago:",
                    options=['TODOS', 'PAGO', 'SIN PAGO'],
                    index=0
                )
            with col_f2:
                # Filtro por Estado de Gestión
                filtro_gestion = st.selectbox(
                    "Estado de Gestión:",
                    options=['TODOS', 'CON GESTIÓN', 'SIN GESTIÓN'],
                    index=0
                )
            with col_f3:
                st.write("Cargo que Gestionó:") # Etiqueta fuera del popover
                # Obtenemos los cargos disponibles
                cargos_disponibles = sorted(df_completo['Cargo_Usuario'].unique())
                
                # Usamos un popover que actúa como un botón desplegable
                with st.popover("Seleccionar Cargos...", use_container_width=True):
                    
                    # Botones para seleccionar/deseleccionar todos rápidamente
                    if st.button("Seleccionar Todos", use_container_width=True, key="select_all_cargos"):
                        for cargo in cargos_disponibles:
                            st.session_state[f"cargo_{cargo}"] = True
                    
                    if st.button("Deseleccionar Todos", use_container_width=True, key="deselect_all_cargos"):
                        for cargo in cargos_disponibles:
                            st.session_state[f"cargo_{cargo}"] = False
                    st.markdown("---")

                    # Creamos un checkbox para cada cargo disponible
                    for cargo in cargos_disponibles:
                        # Inicializamos el estado de cada checkbox si no existe
                        if f"cargo_{cargo}" not in st.session_state:
                            st.session_state[f"cargo_{cargo}"] = True # Por defecto, todos seleccionados
                        
                        st.checkbox(cargo, key=f"cargo_{cargo}")

                filtro_cargos = [cargo for cargo in cargos_disponibles if st.session_state.get(f"cargo_{cargo}", False)]
                st.caption(f"{len(filtro_cargos)} de {len(cargos_disponibles)} cargos seleccionados.")
                
            with col_f4:
                st.write("Excluir créditos gestionados por:")
                with st.popover("Seleccionar para Excluir...", use_container_width=True):
                    if st.button("Excluir Todos", use_container_width=True, key="exclude_all_cargos"):
                        for cargo in cargos_disponibles:
                            st.session_state[f"exclude_cargo_{cargo}"] = True
                    if st.button("No Excluir Ninguno", use_container_width=True, key="exclude_none_cargos"):
                        for cargo in cargos_disponibles:
                            st.session_state[f"exclude_cargo_{cargo}"] = False
                    st.markdown("---")
                    for cargo in cargos_disponibles:
                        # El estado por defecto es NO excluir (False)
                        if f"exclude_cargo_{cargo}" not in st.session_state:
                            st.session_state[f"exclude_cargo_{cargo}"] = False
                        st.checkbox(cargo, key=f"exclude_cargo_{cargo}")

                cargos_a_excluir = [cargo for cargo in cargos_disponibles if st.session_state.get(f"exclude_cargo_{cargo}", False)]
                st.caption(f"{len(cargos_a_excluir)} cargos vetados.")    
                
            df_filtrado = df_completo.copy() # Empezamos con todos los datos
            if cargos_a_excluir:
                 # Paso 1: Identificar todos los créditos únicos que fueron tocados por los cargos a excluir
                creditos_a_excluir_set = set(df_filtrado[df_filtrado['Cargo_Usuario'].isin(cargos_a_excluir)]['Credito'].unique())
                # Paso 2: Eliminar TODAS las filas de esos créditos del dataframe
                if creditos_a_excluir_set:
                    df_filtrado = df_filtrado[~df_filtrado['Credito'].isin(creditos_a_excluir_set)]            
            if filtro_pago != 'TODOS':
                df_filtrado = df_filtrado[df_filtrado['Estado_Pago'] == filtro_pago]
            if filtro_gestion != 'TODOS':
                df_filtrado = df_filtrado[df_filtrado['Estado_Gestion'] == filtro_gestion]
            if filtro_cargos:
                df_filtrado = df_filtrado[df_filtrado['Cargo_Usuario'].isin(filtro_cargos)]
                
            todas_las_columnas_disponibles = [
                'Credito', 'Nombre_Cliente', 'Cedula_Cliente', 'Celular', 'Nombre_Ciudad', 'Zona','Dias_Atraso_Final', 
                'Total_Recaudo', 'Valor_Vencido', 'Estado_Pago','Estado_Gestion', 'Cargo_Usuario','Novedades_Por_Cargo',
                'Codeudor1', 'Nombre_Codeudor1', 'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2','Telefono_Codeudor2', 
                'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente','Empresa'
                # Añade aquí todas las demás columnas que desees
            ]
            columnas_por_defecto = ['Credito', 'Nombre_Cliente', 'Cedula_Cliente', 'Celular', 'Cargo_Usuario','Novedades_Por_Cargo']
            columnas_seleccionadas = st.multiselect(
                "Selecciona las columnas a visualizar en la tabla:",
                options=todas_las_columnas_disponibles,
                default=columnas_por_defecto
            )
            
            # --- Visualización de la Tabla ---
            st.write(f"#### Mostrando {len(df_filtrado)} registros")
            if not columnas_seleccionadas:
                st.warning("Por favor, selecciona al menos una columna para visualizar.")
            elif not df_filtrado.empty:
                # Aseguramos que solo usamos columnas que existen en el dataframe filtrado
                columnas_a_mostrar = [col for col in columnas_seleccionadas if col in df_filtrado.columns]
                st.data_editor(
                    df_filtrado[columnas_a_mostrar],
                    use_container_width=True,
                    hide_index=True,
                    disabled=True, # La tabla es de solo lectura
                    key="editor_busqueda_detallada"
                )
            else:
                st.info("No se encontraron créditos que cumplan con los filtros seleccionados.")
        else:
            st.warning("No hay datos procesados para mostrar en la tabla.")
                        
        
        st.subheader("Seguimiento por Rodammiento")
        # 1. Obtenemos los datos ya agregados
        agg_rodamiento = tab2_data.get("rodamiento_data")
        if agg_rodamiento is not None and not agg_rodamiento.empty:
            # <-- CAMBIO: Ya no creamos el multiselect aquí.
            # El gráfico ahora recibe los datos completos y sin filtrar.
            fig_rodamiento = charts_rodamientos.create_rodamiento_bar_chart(agg_rodamiento)
            if fig_rodamiento:
                st.plotly_chart(fig_rodamiento, use_container_width=True)

        # --- Tabla de Detalle con Filtros Mejorados ---
        st.markdown("---")
        st.subheader("🔍 Detalle de Créditos")

        df_processed_cartera = tab2_data.get("processed_cartera") # Asegúrate de que este es el dataframe correcto
        if df_processed_cartera is not None and not df_processed_cartera.empty:
            
            # --- Creamos un layout organizado para todos los filtros de la tabla ---
            st.write("#### Filtros de Búsqueda")
            col_f1, col_f2, col_f3 = st.columns(3)

            # --- FILTRO 1: Estado de Rodamiento (Popover) ---
            with col_f1:
                st.write("Filtrar por rodamiento:")
                # Aseguramos que agg_rodamiento existe para obtener las opciones
                if agg_rodamiento is not None and not agg_rodamiento.empty:
                    rodamiento_options = sorted(agg_rodamiento['Rodamiento'].unique())
                    with st.popover("Seleccionar Rodamientos...", use_container_width=True):
                        if st.button("Todos", use_container_width=True, key="select_all_rodamiento"):
                            for opt in rodamiento_options: st.session_state[f"rod_{opt}"] = True
                        if st.button("Ninguno", use_container_width=True, key="deselect_all_rodamiento"):
                            for opt in rodamiento_options: st.session_state[f"rod_{opt}"] = False
                        st.markdown("---")
                        for opt in rodamiento_options:
                            if f"rod_{opt}" not in st.session_state:
                                st.session_state[f"rod_{opt}"] = True
                            st.checkbox(opt, key=f"rod_{opt}")
                    
                    selected_rodamientos = [opt for opt in rodamiento_options if st.session_state.get(f"rod_{opt}", True)]
                    st.caption(f"{len(selected_rodamientos)} de {len(rodamiento_options)} seleccionados.")
                else:
                    selected_rodamientos = []
                    st.caption("No hay datos de rodamiento.")

            # --- FILTRO 2: Estado de Gestión (Convertido a Popover) ---
            with col_f2:
                st.write("Filtrar por gestión:")
                gestion_options = ['CON GESTIÓN', 'SIN GESTIÓN']
                with st.popover("Seleccionar Estados...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="select_all_gestion_rod"):
                        for opt in gestion_options: st.session_state[f"gestion_rod_{opt}"] = True
                    if st.button("Ninguno", use_container_width=True, key="deselect_all_gestion_rod"):
                        for opt in gestion_options: st.session_state[f"gestion_rod_{opt}"] = False
                    st.markdown("---")
                    for opt in gestion_options:
                        if f"gestion_rod_{opt}" not in st.session_state:
                            st.session_state[f"gestion_rod_{opt}"] = True
                        st.checkbox(opt, key=f"gestion_rod_{opt}")

                selected_gestiones = [opt for opt in gestion_options if st.session_state.get(f"gestion_rod_{opt}", True)]
                st.caption(f"{len(selected_gestiones)} de {len(gestion_options)} seleccionados.")

            # --- FILTRO 3: NUEVO filtro de Estado de Pago (Popover) ---
            with col_f3:
                st.write("Filtrar por pago:")
                pago_options = ['PAGO', 'SIN PAGO']
                with st.popover("Seleccionar Estados...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="select_all_pago_rod"):
                        for opt in pago_options: st.session_state[f"pago_rod_{opt}"] = True
                    if st.button("Ninguno", use_container_width=True, key="deselect_all_pago_rod"):
                        for opt in pago_options: st.session_state[f"pago_rod_{opt}"] = False
                    st.markdown("---")
                    for opt in pago_options:
                        if f"pago_rod_{opt}" not in st.session_state:
                            st.session_state[f"pago_rod_{opt}"] = True
                        st.checkbox(opt, key=f"pago_rod_{opt}")

                selected_pagos = [opt for opt in pago_options if st.session_state.get(f"pago_rod_{opt}", True)]
                st.caption(f"{len(selected_pagos)} de {len(pago_options)} seleccionados.")

            # --- Lógica para aplicar los filtros a la tabla ---
            df_tabla = df_processed_cartera.copy() # Empezamos con el dataframe completo
    
            # Aplicamos cada filtro si hay selecciones
            if selected_rodamientos:
                df_tabla = df_tabla[df_tabla['Rodamiento'].isin(selected_rodamientos)]
            
            if selected_gestiones:
                df_tabla = df_tabla[df_tabla['Estado_Gestion'].isin(selected_gestiones)]
            
            if selected_pagos:
                df_tabla = df_tabla[df_tabla['Estado_Pago'].isin(selected_pagos)]
                    
            # --- Selector de Columnas (sin cambios) ---
            todas_las_columnas_posibles = [
                'Empresa', 'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 
                'Nombre_Ciudad', 'Zona', 'Codeudor1', 'Nombre_Codeudor1', 'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2', 
                'Telefono_Codeudor2','Dias_Atraso_Final', 'Total_Recaudo',  'Meta_Intereses', 'Meta_Saldo', 'Valor_Vencido','Rodamiento',
                'Rodamiento_Cartera','Estado_Pago', 'Estado_Gestion', 'Empresa'
                
            ]
            columnas_disponibles = [col for col in todas_las_columnas_posibles if col in df_tabla.columns]
            columnas_seleccionadas = st.multiselect(
                "Selecciona las columnas a mostrar en la tabla:",
                options=columnas_disponibles,
                default=['Credito', 'Cedula_Cliente', 'Nombre_Cliente','Celular','Rodamiento','Meta_Saldo', 'Valor_Vencido']
            )
            
            # --- Visualización de la Tabla (sin cambios) ---
            st.info(f"Mostrando {len(df_tabla)} créditos que coinciden con los filtros")
            if not columnas_seleccionadas:
                st.warning("Por favor, selecciona al menos una columna para mostrar en la tabla.")
            elif not df_tabla.empty:
                st.data_editor(
                    df_tabla[columnas_seleccionadas], 
                    use_container_width=True,
                    hide_index=True,
                    disabled=True,
                    key="editor_detalle_rodamiento"
                )
            else:
                st.warning("No se encontraron créditos que coincidan con la selección.")
        else:
            st.info("No hay datos de cartera disponibles para mostrar en la tabla.")


    with tab3:
        st.header("Resultados de Cumplimiento por Zona y Franja")

        # Usamos el dataframe pre-procesado
        if df_resultados is not None and not df_resultados.empty:
            
            # 1. Filtro de zonas (sin cambios)
            zonas_disponibles = sorted(df_resultados['Zona'].unique())
            with st.popover("Selecciona una o más Zonas...", use_container_width=False):
                if st.button("Seleccionar Todas", key="select_all_zonas"):
                    for zona in zonas_disponibles: st.session_state[f"zona_{zona}"] = True
                if st.button("Deseleccionar Todas", key="deselect_all_zonas"):
                    for zona in zonas_disponibles: st.session_state[f"zona_{zona}"] = False
                st.markdown("---")
                for zona in zonas_disponibles:
                    if f"zona_{zona}" not in st.session_state:
                        st.session_state[f"zona_{zona}"] = True
                    st.checkbox(zona, key=f"zona_{zona}")
            
            zonas_seleccionadas = [z for z in zonas_disponibles if st.session_state.get(f"zona_{z}", True)]
            st.caption(f"{len(zonas_seleccionadas)} de {len(zonas_disponibles)} zonas seleccionadas.")
            st.markdown("---")

            # 2. Filtramos el dataframe base (sin cambios)
            df_tabla_base = df_resultados[df_resultados['Zona'].isin(zonas_seleccionadas)]

            if df_tabla_base.empty:
                st.warning("Selecciona al menos una zona para ver los resultados.")
            else:
                # 3. Agregación de datos (sin cambios)
                datos_agregados_charts = df_tabla_base.groupby('Franja_Meta').agg(
                    Meta_Total=('Meta_Total', 'sum'),
                    Recaudo_Total=('Recaudo_Total', 'sum'),
                    Recaudo_Sin_Anti_Total=('Recaudo_Sin_Anti_Total', 'sum'),
                    Recaudo_Meta_Total=('Recaudo_Meta_Total', 'sum')
                ).reset_index()
                datos_agregados_charts['Cumplimiento_%'] = (datos_agregados_charts['Recaudo_Total'] / datos_agregados_charts['Meta_Total']).fillna(0)

                # --- NUEVA SECCIÓN DE GRÁFICOS CON LA DISTRIBUCIÓN DESEADA ---
                
                # Definimos las dos columnas principales: 2/3 para la cuadrícula, 1/3 para el total
                col_izquierda, col_derecha = st.columns([2, 1])

                # --- Columna Izquierda: Cuadrícula de 2x2 para las franjas ---
                with col_izquierda:
                    franjas_a_mostrar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
                    
                    # Creamos dos filas para la cuadrícula
                    fila1_cols = st.columns(2)
                    fila2_cols = st.columns(2)
                    
                    # Combinamos las columnas de ambas filas en una sola lista para iterar
                    grid_cols = fila1_cols + fila2_cols

                    for col, franja in zip(grid_cols, franjas_a_mostrar):
                        with col:
                            data_row = datos_agregados_charts[datos_agregados_charts['Franja_Meta'] == franja]
                            if not data_row.empty:
                                fig_gauge = charts_resultados.create_gauge_chart( # Usamos tu función
                                    value=data_row['Cumplimiento_%'].iloc[0],
                                    meta=data_row['Meta_Total'].iloc[0],
                                    recaudo=data_row['Recaudo_Total'].iloc[0],
                                    faltante=data_row['Meta_Total'].iloc[0] - data_row['Recaudo_Total'].iloc[0],
                                    title=f"{franja}" # Título específico para cada gráfico
                                )
                                st.plotly_chart(fig_gauge, use_container_width=True)
                            else:
                                st.warning(f"Sin datos para franja {franja}.")
            
                # --- Columna Derecha: Gráfico grande para el total ---
                with col_derecha:
                    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
                    total_recaudo_sin_anti = datos_agregados_charts['Recaudo_Sin_Anti_Total'].sum()
                    total_recaudo_meta = datos_agregados_charts['Recaudo_Meta_Total'].sum()
                    cumplimiento_sin_anti = (total_recaudo_sin_anti / total_recaudo_meta) if total_recaudo_meta > 0 else 0
                    
                    titulo_grafico_total = f"T.R ({len(zonas_seleccionadas)} Zonas)"

                    fig_gauge_total = charts_resultados.create_gauge_chart( # Usamos tu función
                        value=cumplimiento_sin_anti,
                        meta=total_recaudo_meta,
                        recaudo=total_recaudo_sin_anti,
                        faltante=total_recaudo_meta - total_recaudo_sin_anti,
                        title=titulo_grafico_total
                    )
                    st.plotly_chart(fig_gauge_total, use_container_width=True)

                # --- Sección de Tablas de Detalle ---
                st.markdown("---")
                st.header("Tabla de Detalle por Zona y Franja")

                expected_compliance, start_date, end_date = charts_resultados.calculate_expected_compliance()
                st.info(f"**Meta de cumplimiento para hoy ({date.today().strftime('%d/%m/%Y')}): {expected_compliance:.2%}** | "
                        f"Periodo: {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}")
                st.markdown("---")

                for franja in franjas_a_mostrar:
                    st.subheader(f"Detalle para Franja: {franja}")
                    df_tabla_franja = df_tabla_base[df_tabla_base['Franja_Meta'] == franja].copy()

                    if df_tabla_franja.empty:
                        st.write("Sin datos para esta franja.")
                        st.markdown("---")
                        continue
                    
                    # Preparación de la tabla para visualización (sin cambios)
                    df_tabla_franja['Faltante ($)'] = df_tabla_franja['Meta_Total'] - df_tabla_franja['Recaudo_Total']
                    df_tabla_display = df_tabla_franja.rename(columns={
                        'Franja_Meta': 'Franja', 'Meta_Total': 'Meta ($)', 'Recaudo_Total': 'Recaudo ($)',
                        'Cumplimiento_%': 'Cumplimiento (%)', 'Regional_Cobro': 'Regional Cobro'
                    })
                    
                    column_order = ['Regional Cobro', 'Zona', 'Franja', 'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)']
                    df_tabla_display = df_tabla_display[[col for col in column_order if col in df_tabla_display.columns]]

                    # 1. Volvemos a generar el objeto de estilo y lo convertimos a HTML
                    styled_df = df_tabla_display.style.map(
                        lambda x: charts_resultados.style_cumplimiento_bar(x, expected_compliance),
                        subset=['Cumplimiento (%)']
                    ).format({
                        'Meta ($)': '${:,.0f}', 'Recaudo ($)': '${:,.0f}',
                        'Faltante ($)': '${:,.0f}', 'Cumplimiento (%)': '{:.2%}'
                    }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
                        {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
                    ])
                    
                    html_table = styled_df.to_html()

                    # 2. Usamos st.markdown para renderizar el HTML con los estilos
                    #    y mantenemos la lógica del scroll
                    if len(df_tabla_display) > 7:
                        st.markdown(
                            f'<div style="width: 100%; max-height: 350px; overflow-y: auto;">{html_table}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(html_table, unsafe_allow_html=True)
                    
                    df_for_excel = df_tabla_display.copy()
                
                    # 2. Aplicamos el formato deseado a la columna 'Cumplimiento (%)'.
                    #    Multiplica por 100, formatea a 2 decimales, reemplaza '.' por ',' y añade '%'.
                    df_for_excel['Cumplimiento (%)'] = df_for_excel['Cumplimiento (%)'].apply(
                        lambda x: f"{x * 100:.2f}".replace('.', ',') + '%'
                    )

                    # 3. Pasamos el nuevo DataFrame formateado a la función de descarga.
                    charts_resultados.generate_excel_download_link( # Asumiendo que está disponible
                        df=df_for_excel,
                        filename=f"detalle_zonas_{franja.replace(' ', '_')}.xlsx",
                        button_label=f"📥 Descargar Datos de Franja {franja}"
                    )
                    st.markdown("---")

                # --- Sección de Métricas Totales ---
                st.subheader("Totales Generales de Zonas Seleccionadas")
                total_meta = df_tabla_base['Meta_Total'].sum()
                total_recaudo = df_tabla_base['Recaudo_Total'].sum()
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Meta Total", f"${total_meta:,.0f}")
                col2.metric("Recaudo Total", f"${total_recaudo:,.0f}")
                col3.metric("Faltante Total", f"${total_meta - total_recaudo:,.0f}")
                col4.metric("Cumplimiento Total", f"{(total_recaudo / total_meta) if total_meta > 0 else 0:.2%}")

        else:
            st.warning("No se encontraron datos de resultados para los filtros globales seleccionados.")

    with tab4:
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

    with tab5:
        st.header("Potenciales Clientes para Retanqueo")
        
        # 1. Llamamos a la función con la nueva lógica para obtener los clientes potenciales
        df_potenciales = charts_retanqueos.prepare_retanqueos_data(df_cartera_filtrada)

        if df_potenciales.empty:
            st.info("No se encontraron clientes que cumplan con los criterios de retanqueo para los filtros globales seleccionados.")
        else:
            # --- CAMBIO: Creación de Filtros en 3 columnas (se eliminó el de tipo de crédito) ---
            st.write("#### Filtros Específicos")
            col_f1, col_f2, col_f3 = st.columns(3)

            with col_f1:
                # Filtro por Vendedor Activo/Inactivo (sin cambios)
                opciones_vendedor_activo = sorted(df_potenciales["Vendedor_Activo"].unique())
                filtro_vendedor_activo = st.selectbox(
                    "Estado del Vendedor:",
                    options=['TODOS'] + opciones_vendedor_activo,
                    index=0
                )

            with col_f2:
                # Filtro Popover para Nombre_Vendedor (movido a la segunda columna)
                vendedores_disponibles = sorted(df_potenciales['Nombre_Vendedor'].unique())
                with st.popover("Seleccionar Vendedores...", use_container_width=True):
                    if st.button("Seleccionar Todos", key="select_all_vendedores"):
                        for vendedor in vendedores_disponibles: st.session_state[f"vend_{vendedor}"] = True
                    if st.button("Deseleccionar Todos", key="deselect_all_vendedores"):
                        for vendedor in vendedores_disponibles: st.session_state[f"vend_{vendedor}"] = False
                    st.markdown("---")
                    for vendedor in vendedores_disponibles:
                        if f"vend_{vendedor}" not in st.session_state:
                            st.session_state[f"vend_{vendedor}"] = True
                        st.checkbox(vendedor, key=f"vend_{vendedor}")
                
                vendedores_seleccionados = [v for v in vendedores_disponibles if st.session_state.get(f"vend_{v}", True)]
                st.caption(f"{len(vendedores_seleccionados)} de {len(vendedores_disponibles)} vendedores seleccionados.")

            with col_f3:
                # Filtro Popover para Regional_Venta (movido a la tercera columna)
                if 'Regional_Venta' in df_potenciales.columns:
                    regionales_disponibles = sorted(df_potenciales['Regional_Venta'].unique())
                    with st.popover("Seleccionar Regionales...", use_container_width=True):
                        if st.button("Seleccionar Todas", key="select_all_regionales"):
                            for regional in regionales_disponibles: st.session_state[f"reg_{regional}"] = True
                        if st.button("Deseleccionar Todos", key="deselect_all_regionales"):
                            for regional in regionales_disponibles: st.session_state[f"reg_{regional}"] = False
                        st.markdown("---")
                        for regional in regionales_disponibles:
                            if f"reg_{regional}" not in st.session_state:
                                st.session_state[f"reg_{regional}"] = True
                            st.checkbox(regional, key=f"reg_{regional}")
                    
                    regionales_seleccionadas = [r for r in regionales_disponibles if st.session_state.get(f"reg_{r}", True)]
                    st.caption(f"{len(regionales_seleccionadas)} de {len(regionales_disponibles)} regionales seleccionadas.")
                else:
                    regionales_seleccionadas = []
                    st.caption("No hay datos de Regional Venta.")

            # --- CAMBIO: Lógica de filtrado simplificada ---
            df_filtrado_tabla = df_potenciales.copy()
            if filtro_vendedor_activo != 'TODOS':
                df_filtrado_tabla = df_filtrado_tabla[df_filtrado_tabla['Vendedor_Activo'] == filtro_vendedor_activo]
            # Se eliminó el filtro por 'Tipo_Credito'
            if vendedores_seleccionados:
                df_filtrado_tabla = df_filtrado_tabla[df_filtrado_tabla['Nombre_Vendedor'].isin(vendedores_seleccionados)]
            if 'Regional_Venta' in df_filtrado_tabla.columns and regionales_seleccionadas:
                df_filtrado_tabla = df_filtrado_tabla[df_filtrado_tabla['Regional_Venta'].isin(regionales_seleccionadas)]
                
            # --- Selector de Columnas (con defaults actualizados) ---
            columnas_disponibles_tabla = [
                'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 'Direccion',
                'Valor_Desembolso', 'Meta_Saldo', 'Total_Cuotas', 'Cuotas_Restantes', 'Dias_Atraso_Final',
                'Vendedor_Activo','Nombre_Vendedor', 'Regional_Venta', 'Nombre_Producto','Cuotas_Pagadas'
            ]
            # Columnas por defecto que muestran la información clave de la nueva lógica
            columnas_por_defecto_tabla = [
                'Credito', 'Nombre_Cliente','Celular', 'Total_Cuotas','Cuotas_Pagadas', 'Cuotas_Restantes', 'Dias_Atraso_Final', 'Nombre_Vendedor'
            ]

            columnas_seleccionadas = st.multiselect(
                "Selecciona las columnas a visualizar:",
                options=columnas_disponibles_tabla,
                default=[col for col in columnas_por_defecto_tabla if col in df_filtrado_tabla.columns]
            )
            
            st.info(f"Mostrando {len(df_filtrado_tabla)} clientes potenciales para retanqueo.")
            if not columnas_seleccionadas:
                st.warning("Selecciona al menos una columna para ver la tabla.")
            else:
                st.dataframe(
                    df_filtrado_tabla[columnas_seleccionadas],
                    use_container_width=True,
                    hide_index=True
                )
if __name__ == "__main__":
    main()