import streamlit as st
import charts_rodamientos

def render(tab2_data):
    """
    Renderiza el contenido de la pestaña "Seguimientos y Gestión".
    """

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