import streamlit as st 

def render(tab5_data):
    st.header("Potenciales Clientes para Retanqueo")
    # 1. Usamos el dataframe del diccionario devuelto por la nueva función
    df_potenciales = tab5_data["potenciales_retanqueo"]

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