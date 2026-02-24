import streamlit as st
import pandas as pd
import charts_rodamientos

def render(tab2_data):
    """
    Renderiza el contenido con una distribución COMPACTA de alta densidad.
    """
    st.header("Seguimientos y Gestión")

    col1, col2, col3 = st.columns([1, 1, 0.8], gap="small")
    # --- COLUMNA 1: RECAUDO
    with col1:
        with st.container(border=True):
            st.markdown("<h5 style='text-align: center; margin-bottom: 0;'>Recaudo General</h5>", unsafe_allow_html=True)
            conteo_estados_donut = tab2_data.get("donut_data")
            donut_chart_fig = charts_rodamientos.create_recaudo_donut_chart(
                conteo_estados_donut,
                estado_seleccionado="TODOS",
                show_center_text=False
            )
            if donut_chart_fig:
                # height=420 llena la columna verticalmente. Margenes en 0 eliminan espacio blanco.
                donut_chart_fig.update_layout(
                    height=420, 
                    margin=dict(t=30, b=10, l=10, r=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(donut_chart_fig, use_container_width=True)
            else:
                st.info("Sin datos.")

    # --- COLUMNA 2: GESTIÓN GLOBAL (MACRO) ---
    with col2:
        with st.container(border=True):
            st.markdown("<h5 style='text-align: center; margin-bottom: 0;'>Gestión Global</h5>", unsafe_allow_html=True)
            grouped_data_todos = tab2_data.get("sunburst_initial_grouped")
            conteo_data_todos = tab2_data.get("sunburst_initial_counts")
            
            sunburst_todos_fig = charts_rodamientos.create_nested_pie_chart(
                grouped_data_todos,
                conteo_data_todos,
                height=420 # Igualamos altura a la columna 1
            )
            if sunburst_todos_fig:
                # Ajustamos márgenes agresivamente
                sunburst_todos_fig.update_layout(margin=dict(t=30, b=10, l=10, r=10))
                st.plotly_chart(sunburst_todos_fig, use_container_width=True)
            else:
                st.info("Sin datos.")

    # --- COLUMNA 3: DETALLES (APILADOS) ---
    with col3:
        # GRÁFICO SUPERIOR: CON PAGO
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center; margin: 0; color: #28a745;'>Créditos CON PAGO</h6>", unsafe_allow_html=True)
            grouped_data_pago, conteo_data_pago = tab2_data.get("detalle_pago", (None, None))
            sunburst_pago_fig = charts_rodamientos.create_nested_pie_chart(
                grouped_data_pago,
                conteo_data_pago,
                height=180 # Altura reducida (mitad aprox)
            )
            if sunburst_pago_fig:
                sunburst_pago_fig.update_layout(margin=dict(t=20, b=10, l=10, r=10))
                st.plotly_chart(sunburst_pago_fig, use_container_width=True)
            else:
                st.write("Sin datos.")

        # GRÁFICO INFERIOR: SIN PAGO
        with st.container(border=True):
            st.markdown("<h6 style='text-align: center; margin: 0; color: #dc3545;'>Créditos SIN PAGO</h6>", unsafe_allow_html=True)
            grouped_data_sin_pago, conteo_data_sin_pago = tab2_data.get("detalle_sin_pago", (None, None))
            detalle_sin_pago_fig = charts_rodamientos.create_nested_pie_chart(
                grouped_data_sin_pago,
                conteo_data_sin_pago,
                height=180 # Altura reducida (mitad aprox)
            )
            if detalle_sin_pago_fig:
                detalle_sin_pago_fig.update_layout(margin=dict(t=20, b=10, l=10, r=10))
                st.plotly_chart(detalle_sin_pago_fig, use_container_width=True)
            else:
                st.write("Sin datos.")

    st.markdown("---")

    # --- TABLA 1: DETALLE DE CRÉDITOS CON GESTIÓN ---
    st.header("Detalle de Créditos con Gestión")
    df_completo = tab2_data.get("data_para_tabla")

    if df_completo is not None and not df_completo.empty:
        
        # Filtros organizados
        with st.expander("Filtros de Búsqueda (Gestión)", expanded=False): # Expanded=False para limpiar vista inicial
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)

            # --- FILTRO 1: Estado de Pago ---
            with col_f1:
                st.write("**Estado de Pago**")
                opciones_pago_gral = ['PAGO', 'SIN PAGO']
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="sel_all_pago_gral"):
                        for opt in opciones_pago_gral: st.session_state[f"pago_gral_{opt}"] = True
                    if st.button("Ninguno", use_container_width=True, key="desel_all_pago_gral"):
                        for opt in opciones_pago_gral: st.session_state[f"pago_gral_{opt}"] = False
                    st.divider()
                    for opt in opciones_pago_gral:
                        if f"pago_gral_{opt}" not in st.session_state:
                            st.session_state[f"pago_gral_{opt}"] = True
                        st.checkbox(opt, key=f"pago_gral_{opt}")
                
                seleccion_pago_gral = [opt for opt in opciones_pago_gral if st.session_state.get(f"pago_gral_{opt}", True)]
                st.caption(f"{len(seleccion_pago_gral)} seleccionados.")

            # --- FILTRO 2: Estado de Gestión ---
            with col_f2:
                st.write("**Estado de Gestión**")
                opciones_gestion_gral = ['CON GESTIÓN', 'SIN GESTIÓN']
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="sel_all_gest_gral"):
                        for opt in opciones_gestion_gral: st.session_state[f"gest_gral_{opt}"] = True
                    if st.button("Ninguno", use_container_width=True, key="desel_all_gest_gral"):
                        for opt in opciones_gestion_gral: st.session_state[f"gest_gral_{opt}"] = False
                    st.divider()
                    for opt in opciones_gestion_gral:
                        if f"gest_gral_{opt}" not in st.session_state:
                            st.session_state[f"gest_gral_{opt}"] = True
                        st.checkbox(opt, key=f"gest_gral_{opt}")
                
                seleccion_gestion_gral = [opt for opt in opciones_gestion_gral if st.session_state.get(f"gest_gral_{opt}", True)]
                st.caption(f"{len(seleccion_gestion_gral)} seleccionados.")

            # --- FILTRO 3: Cargos ---
            with col_f3:
                st.write("**Cargo Usuario**") 
                
                # --- CORRECCIÓN AQUÍ ---
                # 1. Obtenemos los valores únicos
                cargos_crudos = df_completo['Cargo_Usuario'].unique()
                # 2. Convertimos todo a string y filtramos los nulos/nan
                cargos_limpios = [str(c) for c in cargos_crudos if pd.notna(c) and str(c).strip().lower() != 'nan']
                # 3. Ordenamos de forma segura (todo es texto)
                cargos_disponibles = sorted(list(set(cargos_limpios)))
                
                with st.popover("Seleccionar Cargos...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="select_all_cargos"):
                        for cargo in cargos_disponibles: st.session_state[f"cargo_{cargo}"] = True
                    if st.button("Ninguno", use_container_width=True, key="deselect_all_cargos"):
                        for cargo in cargos_disponibles: st.session_state[f"cargo_{cargo}"] = False
                    st.divider()
                    for cargo in cargos_disponibles:
                        if f"cargo_{cargo}" not in st.session_state:
                            st.session_state[f"cargo_{cargo}"] = True 
                        st.checkbox(cargo, key=f"cargo_{cargo}")

                filtro_cargos = [cargo for cargo in cargos_disponibles if st.session_state.get(f"cargo_{cargo}", False)]
                st.caption(f"{len(filtro_cargos)} cargos.")
                
            # --- FILTRO 4: Excluir Cargos ---
            with col_f4:
                st.write("**Excluir Cargos**")
                with st.popover("Seleccionar Exclusión...", use_container_width=True):
                    if st.button("Excluir Todos", use_container_width=True, key="exclude_all_cargos"):
                        for cargo in cargos_disponibles: st.session_state[f"exclude_cargo_{cargo}"] = True
                    if st.button("Limpiar", use_container_width=True, key="exclude_none_cargos"):
                        for cargo in cargos_disponibles: st.session_state[f"exclude_cargo_{cargo}"] = False
                    st.divider()
                    for cargo in cargos_disponibles:
                        if f"exclude_cargo_{cargo}" not in st.session_state:
                            st.session_state[f"exclude_cargo_{cargo}"] = False
                        st.checkbox(cargo, key=f"exclude_cargo_{cargo}")

                cargos_a_excluir = [cargo for cargo in cargos_disponibles if st.session_state.get(f"exclude_cargo_{cargo}", False)]
                st.caption(f"{len(cargos_a_excluir)} vetados.")     
            
        # --- APLICACIÓN DE FILTROS ---
        df_filtrado = df_completo.copy() 

        # 1. Lógica de Exclusión
        if cargos_a_excluir:
            creditos_a_excluir_set = set(df_filtrado[df_filtrado['Cargo_Usuario'].isin(cargos_a_excluir)]['Credito'].unique())
            if creditos_a_excluir_set:
                df_filtrado = df_filtrado[~df_filtrado['Credito'].isin(creditos_a_excluir_set)]            
        
        # 2. Filtros de Selección Múltiple
        if seleccion_pago_gral:
            df_filtrado = df_filtrado[df_filtrado['Estado_Pago'].isin(seleccion_pago_gral)]
        
        if seleccion_gestion_gral:
            df_filtrado = df_filtrado[df_filtrado['Estado_Gestion'].isin(seleccion_gestion_gral)]
            
        if filtro_cargos:
            df_filtrado = df_filtrado[df_filtrado['Cargo_Usuario'].isin(filtro_cargos)]
            
        # --- SELECCIÓN DE COLUMNAS ---
        todas_las_columnas_disponibles = [
            'Empresa','Credito', 'Nombre_Cliente', 'Cedula_Cliente', 'Celular', 'Nombre_Ciudad', 'Zona','Dias_Atraso_Final', 
            'Total_Recaudo', 'Valor_Vencido', 'Estado_Pago','Estado_Gestion', 'Cargo_Usuario','Novedades_Por_Cargo',
            'Codeudor1', 'Nombre_Codeudor1', 'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2','Telefono_Codeudor2', 
            'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente','Meta_$','Novedad', 'Tipo_Novedad', 'Nombre_Usuario'
        ]
        columnas_por_defecto = ['Credito', 'Nombre_Cliente', 'Cedula_Cliente', 'Celular', 'Cargo_Usuario','Novedad','Tipo_Novedad', 'Novedades_Por_Cargo']
        
        with st.expander("Personalizar Columnas de la Tabla"):
            columnas_seleccionadas = st.multiselect(
                "Columnas visibles:",
                options=todas_las_columnas_disponibles,
                default=columnas_por_defecto,
                key="multi_cols_gestion_gral",
                label_visibility="collapsed"
            )
        
        st.markdown(f"**Resultados:** {len(df_filtrado)} registros encontrados.")
        if not columnas_seleccionadas:
            st.warning("Selecciona al menos una columna.")
        elif not df_filtrado.empty:
            columnas_a_mostrar = [col for col in columnas_seleccionadas if col in df_filtrado.columns]
            st.data_editor(
                df_filtrado[columnas_a_mostrar],
                use_container_width=True,
                hide_index=True,
                disabled=True,
                key="editor_busqueda_detallada",
                height=400 # Altura fija para mejor UX
            )
        else:
            st.info("No se encontraron créditos con los filtros actuales.")
    else:
        st.warning("No hay datos procesados para mostrar en la tabla.")
    st.markdown("---")

    # SECCIÓN RODAMIENTOS
    st.subheader("Análisis por Rodamiento")
    
    # Usamos container para el gráfico de barras para darle marco
    with st.container(border=True):
        agg_rodamiento = tab2_data.get("rodamiento_data")
        if agg_rodamiento is not None and not agg_rodamiento.empty:
            fig_rodamiento = charts_rodamientos.create_rodamiento_bar_chart(agg_rodamiento)
            if fig_rodamiento:
                # Ajustamos altura del gráfico de barras
                fig_rodamiento.update_layout(height=400)
                st.plotly_chart(fig_rodamiento, use_container_width=True)
        else:
            st.info("No hay datos de rodamiento para graficar.")

    st.markdown("### Detalle de Cartera (Rodamientos)")
    df_processed_cartera = tab2_data.get("processed_cartera")
    
    if df_processed_cartera is not None and not df_processed_cartera.empty:
        
        with st.expander("Filtros de Búsqueda (Rodamientos)", expanded=False):
            col_f1, col_f2, col_f3 = st.columns(3)

            # --- FILTRO 1: Estado de Rodamiento ---
            with col_f1:
                st.write("**Rodamiento**")
                if agg_rodamiento is not None and not agg_rodamiento.empty:
                    rodamiento_options = sorted(agg_rodamiento['Rodamiento'].unique())
                    with st.popover("Seleccionar...", use_container_width=True):
                        if st.button("Todos", use_container_width=True, key="select_all_rodamiento"):
                            for opt in rodamiento_options: st.session_state[f"rod_{opt}"] = True
                        if st.button("Ninguno", use_container_width=True, key="deselect_all_rodamiento"):
                            for opt in rodamiento_options: st.session_state[f"rod_{opt}"] = False
                        st.divider()
                        for opt in rodamiento_options:
                            if f"rod_{opt}" not in st.session_state:
                                st.session_state[f"rod_{opt}"] = True
                            st.checkbox(opt, key=f"rod_{opt}")
                    
                    selected_rodamientos = [opt for opt in rodamiento_options if st.session_state.get(f"rod_{opt}", True)]
                    st.caption(f"{len(selected_rodamientos)} seleccionados.")
                else:
                    selected_rodamientos = []

            # --- FILTRO 2: Estado de Gestión ---
            with col_f2:
                st.write("**Gestión**")
                gestion_options = ['CON GESTIÓN', 'SIN GESTIÓN']
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="select_all_gestion_rod"):
                        for opt in gestion_options: st.session_state[f"gestion_rod_{opt}"] = True
                    if st.button("Ninguno", use_container_width=True, key="deselect_all_gestion_rod"):
                        for opt in gestion_options: st.session_state[f"gestion_rod_{opt}"] = False
                    st.divider()
                    for opt in gestion_options:
                        if f"gestion_rod_{opt}" not in st.session_state:
                            st.session_state[f"gestion_rod_{opt}"] = True
                        st.checkbox(opt, key=f"gestion_rod_{opt}")

                selected_gestiones = [opt for opt in gestion_options if st.session_state.get(f"gestion_rod_{opt}", True)]
                st.caption(f"{len(selected_gestiones)} seleccionados.")

            # --- FILTRO 3: Estado de Pago ---
            with col_f3:
                st.write("**Pago**")
                pago_options = ['PAGO', 'SIN PAGO']
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="select_all_pago_rod"):
                        for opt in pago_options: st.session_state[f"pago_rod_{opt}"] = True
                    if st.button("Ninguno", use_container_width=True, key="deselect_all_pago_rod"):
                        for opt in pago_options: st.session_state[f"pago_rod_{opt}"] = False
                    st.divider()
                    for opt in pago_options:
                        if f"pago_rod_{opt}" not in st.session_state:
                            st.session_state[f"pago_rod_{opt}"] = True
                        st.checkbox(opt, key=f"pago_rod_{opt}")

                selected_pagos = [opt for opt in pago_options if st.session_state.get(f"pago_rod_{opt}", True)]
                st.caption(f"{len(selected_pagos)} seleccionados.")

        # --- APLICACIÓN DE FILTROS RODAMIENTO ---
        df_tabla = df_processed_cartera.copy()

        if selected_rodamientos:
            df_tabla = df_tabla[df_tabla['Rodamiento'].isin(selected_rodamientos)]
        
        if selected_gestiones:
            df_tabla = df_tabla[df_tabla['Estado_Gestion'].isin(selected_gestiones)]
        
        if selected_pagos:
            df_tabla = df_tabla[df_tabla['Estado_Pago'].isin(selected_pagos)]
                
        todas_las_columnas_posibles = [
            'Empresa', 'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente',
            'Nombre_Ciudad', 'Zona', 'Codeudor1', 'Nombre_Codeudor1', 'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2', 'Franja_Cartera',
            'Telefono_Codeudor2','Dias_Atraso_Final', 'Total_Recaudo', 'Meta_Intereses', 'Meta_Saldo', 'Valor_Vencido','Rodamiento',
            'Rodamiento_Cartera','Estado_Pago', 'Estado_Gestion', 'Meta_$'
        ]
        columnas_disponibles = [col for col in todas_las_columnas_posibles if col in df_tabla.columns]
        
        with st.expander("Personalizar Columnas (Rodamientos)"):
            columnas_seleccionadas = st.multiselect(
                "Columnas visibles:",
                options=columnas_disponibles,
                default=['Credito', 'Cedula_Cliente', 'Nombre_Cliente','Celular','Franja_Cartera','Rodamiento','Meta_$','Meta_Saldo','Meta_Intereses', 'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente', 'Valor_Vencido'],
                key="multi_cols_rodamientos",
                label_visibility="collapsed"
            )
        
        st.markdown(f"**Resultados:** {len(df_tabla)} créditos encontrados.")
        if not columnas_seleccionadas:
            st.warning("Selecciona al menos una columna.")
        elif not df_tabla.empty:
            st.data_editor(
                df_tabla[columnas_seleccionadas], 
                use_container_width=True,
                hide_index=True,
                disabled=True,
                key="editor_detalle_rodamiento",
                height=400
            )
        else:
            st.warning("No se encontraron créditos que coincidan con la selección.")
    else:
        st.info("No hay datos de cartera disponibles para mostrar en la tabla.")        