import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def render(data):
    # Desempaquetar los dataframes del diccionario
    df_fnz = data.get("data_fnz")
    df_potenciales = data.get("potenciales_retanqueo")
    df_cosechas = data.get("data_cosechas")
    st.header("Gestión Comercial")
    
    # SECCIÓN 1: ANÁLISIS DE GESTIÓN FNZ007
    st.subheader("Análisis de Gestión FNZ007")

    if df_fnz is not None and not df_fnz.empty:
        
        # --- 1. Filtros Generales FNZ ---
        # Usamos expanded=False para que no estorbe si ya se filtró o al inicio
        with st.expander("Filtros FNZ007", expanded=False):
            col_fnz1, col_fnz2, col_fnz3 = st.columns(3)
            
            with col_fnz1:
                opciones_estado = sorted(df_fnz['Estado'].astype(str).unique())
                filtro_estado = st.multiselect("Estado", options=opciones_estado, placeholder="Todos")
            
            with col_fnz2:
                opciones_analista = sorted(df_fnz['Analista_Asociado'].astype(str).unique())
                filtro_analista = st.multiselect("Analista Asociado", options=opciones_analista, placeholder="Todos")
            
            with col_fnz3:
                opciones_regional = sorted(df_fnz['Regional_Venta'].astype(str).unique())
                filtro_regional = st.multiselect("Regional Venta", options=opciones_regional, placeholder="Todos")

        # --- 2. Aplicar Lógica de Filtrado FNZ ---
        df_fnz_filtrado = df_fnz.copy()
        
        if filtro_estado:
            df_fnz_filtrado = df_fnz_filtrado[df_fnz_filtrado['Estado'].isin(filtro_estado)]
        if filtro_analista:
            df_fnz_filtrado = df_fnz_filtrado[df_fnz_filtrado['Analista_Asociado'].isin(filtro_analista)]
        if filtro_regional:
            df_fnz_filtrado = df_fnz_filtrado[df_fnz_filtrado['Regional_Venta'].isin(filtro_regional)]

        st.caption(f"Registros FNZ visualizados: **{len(df_fnz_filtrado)}**")

        if not df_fnz_filtrado.empty:
            
            # --- 3. Tabla Pivote (Vendedores vs Estado) ---
            st.write("#### Resumen por Vendedor y Estado")
            
            tabla_pivote = pd.crosstab(
                index=df_fnz_filtrado['Nombre_Vendedor'], 
                columns=df_fnz_filtrado['Estado'],
                margins=True, 
                margins_name="Total General"
            )
            
            tabla_visual = tabla_pivote.drop("Total General", axis=0).sort_values("Total General", ascending=False)
            
            col_tabla, col_grafico = st.columns([1, 1], gap="medium")
            
            with col_tabla:
                # Usamos data_editor aquí también para que se vea bonito y ordenable
                st.data_editor(tabla_visual, use_container_width=True, height=400, disabled=True)
                
            with col_grafico:
                df_grafico = df_fnz_filtrado.groupby(['Nombre_Vendedor', 'Estado']).size().reset_index(name='Cantidad')
                top_vendedores = df_grafico.groupby('Nombre_Vendedor')['Cantidad'].sum().nlargest(15).index
                df_grafico_top = df_grafico[df_grafico['Nombre_Vendedor'].isin(top_vendedores)]
                
                fig = px.bar(
                    df_grafico_top, x='Nombre_Vendedor', y='Cantidad', color='Estado',
                    title="Top 15 Vendedores (Volumen)", barmode='stack'
                )
                # Ajustamos márgenes para ganar espacio
                fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

            # --- 4. Detalle de Registros Personalizable (OPTIMIZADO) ---
            st.divider()
            
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.write("#### Detalle de Registros FNZ")
            with col_h2:
                 st.markdown(f"<div style='text-align: right; color: gray;'>Total: {len(df_fnz_filtrado)}</div>", unsafe_allow_html=True)
            
            cols_disponibles_fnz = list(df_fnz.columns)
            cols_default_fnz = [c for c in ['Fecha', 'Cedula_Cliente', 'Nombres', 'Nombre_Vendedor', 'Valor_Total', 'Estado'] if c in cols_disponibles_fnz]

            # --- CAMBIO CLAVE: Selector oculto en Expander ---
            with st.expander("Personalizar Columnas (FNZ)", expanded=False):
                cols_seleccionadas_fnz = st.multiselect(
                    "Columnas visibles:",
                    options=cols_disponibles_fnz,
                    default=cols_default_fnz,
                    key="multiselect_cols_fnz",
                    label_visibility="collapsed"
                )
            
            if cols_seleccionadas_fnz:
                st.data_editor(
                    df_fnz_filtrado[cols_seleccionadas_fnz],
                    use_container_width=True,
                    hide_index=True,
                    disabled=True, # Modo lectura, pero permite ordenar y copiar
                    key="editor_fnz_detail"
                )
            else:
                st.warning("Selecciona al menos una columna.")
        else:
            st.warning("No hay datos FNZ con los filtros seleccionados.")
    else:
        st.info("No se encontró información cargada para FNZ007.")

    # SECCIÓN 2: POTENCIALES CLIENTES PARA RETANQUEO
    st.markdown("---")
    st.header("Potenciales Clientes para Retanqueo")

    if df_potenciales is None or df_potenciales.empty:
        st.info("No se encontraron clientes que cumplan con los criterios.")
    else:
        
        # Filtros colapsados por defecto para limpieza visual
        with st.expander("Filtros de Búsqueda (Retanqueo)", expanded=False):
            col_f1, col_f2, col_f3 = st.columns(3)

            # --- FILTRO 1: Vendedor Activo ---
            with col_f1:
                st.write("**Estado Vendedor**")
                opciones_activo = sorted(df_potenciales["Vendedor_Activo"].astype(str).unique())
                
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", use_container_width=True, key="sel_all_activo_ret"):
                        for opt in opciones_activo: st.session_state[f"ret_activo_{opt}"] = True
                    if st.button("Ninguno", use_container_width=True, key="desel_all_activo_ret"):
                        for opt in opciones_activo: st.session_state[f"ret_activo_{opt}"] = False
                    st.divider()
                    for opt in opciones_activo:
                        if f"ret_activo_{opt}" not in st.session_state: st.session_state[f"ret_activo_{opt}"] = True
                        st.checkbox(opt, key=f"ret_activo_{opt}")
                
                seleccion_vendedor_activo = [opt for opt in opciones_activo if st.session_state.get(f"ret_activo_{opt}", True)]
                st.caption(f"{len(seleccion_vendedor_activo)} seleccionados.")

            # --- FILTRO 2: Nombre Vendedor ---
            with col_f2:
                st.write("**Vendedores**")
                vendedores_disponibles = sorted(df_potenciales['Nombre_Vendedor'].astype(str).unique())
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="select_all_vendedores_ret"):
                        for vendedor in vendedores_disponibles: st.session_state[f"ret_vend_{vendedor}"] = True
                    if st.button("Ninguno", key="deselect_all_vendedores_ret"):
                        for vendedor in vendedores_disponibles: st.session_state[f"ret_vend_{vendedor}"] = False
                    st.divider()
                    for vendedor in vendedores_disponibles:
                        if f"ret_vend_{vendedor}" not in st.session_state: st.session_state[f"ret_vend_{vendedor}"] = True
                        st.checkbox(vendedor, key=f"ret_vend_{vendedor}")
            
                vendedores_seleccionados = [v for v in vendedores_disponibles if st.session_state.get(f"ret_vend_{v}", True)]
                st.caption(f"{len(vendedores_seleccionados)} seleccionados.")

            # --- FILTRO 3: Regional Venta ---
            with col_f3:
                st.write("**Regionales**")
                if 'Regional_Venta' in df_potenciales.columns:
                    regionales_disponibles = sorted(df_potenciales['Regional_Venta'].astype(str).unique())
                    with st.popover("Seleccionar...", use_container_width=True):
                        if st.button("Todas", key="select_all_regionales_ret"):
                            for regional in regionales_disponibles: st.session_state[f"ret_reg_{regional}"] = True
                        if st.button("Ninguna", key="deselect_all_regionales_ret"):
                            for regional in regionales_disponibles: st.session_state[f"ret_reg_{regional}"] = False
                        st.divider()
                        for regional in regionales_disponibles:
                            if f"ret_reg_{regional}" not in st.session_state: st.session_state[f"ret_reg_{regional}"] = True
                            st.checkbox(regional, key=f"ret_reg_{regional}")
                
                    regionales_seleccionadas = [r for r in regionales_disponibles if st.session_state.get(f"ret_reg_{r}", True)]
                    st.caption(f"{len(regionales_seleccionadas)} seleccionadas.")
                else:
                    regionales_seleccionadas = []
                    st.caption("Sin datos.")

        # --- Lógica de filtrado ---
        df_filtrado_tabla = df_potenciales.copy()
        
        if seleccion_vendedor_activo:
             df_filtrado_tabla = df_filtrado_tabla[df_filtrado_tabla['Vendedor_Activo'].astype(str).isin(seleccion_vendedor_activo)]
        if vendedores_seleccionados:
            df_filtrado_tabla = df_filtrado_tabla[df_filtrado_tabla['Nombre_Vendedor'].astype(str).isin(vendedores_seleccionados)]
        if 'Regional_Venta' in df_filtrado_tabla.columns and regionales_seleccionadas:
            df_filtrado_tabla = df_filtrado_tabla[df_filtrado_tabla['Regional_Venta'].astype(str).isin(regionales_seleccionadas)]
            
        # --- Selector de Columnas OPTIMIZADO ---
        columnas_disponibles_tabla = [
            'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 'Direccion',
            'Valor_Desembolso', 'Meta_Saldo', 'Total_Cuotas', 'Cuotas_Restantes', 'Dias_Atraso_Final',
            'Vendedor_Activo','Nombre_Vendedor', 'Regional_Venta', 'Nombre_Producto','Cuotas_Pagadas'
        ]
        
        columnas_por_defecto_tabla = [
            'Credito', 'Nombre_Cliente','Celular', 'Total_Cuotas','Cuotas_Pagadas', 'Cuotas_Restantes', 'Dias_Atraso_Final', 'Nombre_Vendedor'
        ]
        default_cols = [col for col in columnas_por_defecto_tabla if col in df_filtrado_tabla.columns]

        # Texto informativo limpio
        st.markdown(f"**Resultados:** {len(df_filtrado_tabla)} clientes potenciales.")

        # --- CAMBIO CLAVE: Selector oculto en Expander ---
        with st.expander("Personalizar Columnas (Retanqueo)", expanded=False):
            columnas_seleccionadas = st.multiselect(
                "Selecciona las columnas visibles:",
                options=columnas_disponibles_tabla,
                default=default_cols,
                key="multiselect_cols_retanqueo",
                label_visibility="collapsed"
            )
        
        if not columnas_seleccionadas:
            st.warning("Selecciona al menos una columna.")
        else:
            # Data Editor para mejor interactividad
            st.data_editor(
                df_filtrado_tabla[columnas_seleccionadas],
                use_container_width=True,
                hide_index=True,
                disabled=True,
                key="editor_retanqueo"
            )
    st.markdown("---")

    st.header("Seguimiento a Créditos Nuevos (Últimos 6 Meses)")
    st.info("Visualizando créditos con desembolso reciente que presentan mora actualmente.")

    if df_cosechas is not None and not df_cosechas.empty:
        
        # Columnas que quieres mostrar en las tablas
        columnas_visibles = [
            'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 'Direccion',
            'Fecha_Desembolso', 'Valor_Desembolso', 'Cuotas_Pagadas','Primera_Cuota_Mora','Fecha_Ultimo_pago', 
            'Cuota_Vigente','Fecha_Cuota_Vigente','Total_Cuotas','Dias_Atraso_Final', 'Valor_Vencido', 'Nombre_Vendedor'
        ]
        
        # Aseguramos que existan en el DF
        columnas_finales = [c for c in columnas_visibles if c in df_cosechas.columns]

        # --- TABLA 1: NO PAGÓ LA PRIMERA CUOTA ---
        st.subheader("Alerta Crítica: No pagaron la 1ra Cuota")
        df_sec1 = df_cosechas[df_cosechas['Grupo_Seguimiento'] == 'SECCION_1_SIN_PAGO']
        
        if not df_sec1.empty:
            st.markdown(f"**Clientes encontrados:** {len(df_sec1)}")
            st.dataframe(
                df_sec1[columnas_finales],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No hay clientes nuevos debiendo la primera cuota.")

        st.divider()

        # --- TABLA 2: PAGÓ LA 1RA, FALLÓ LA 2DA ---
        st.subheader("Riesgo Alto: Pagaron 1ra, fallaron en la 2da")
        df_sec2 = df_cosechas[df_cosechas['Grupo_Seguimiento'] == 'SECCION_2_FALLO_2DA']
        
        if not df_sec2.empty:
            st.markdown(f"**Clientes encontrados:** {len(df_sec2)}")
            st.dataframe(
                df_sec2[columnas_finales],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No hay clientes nuevos que fallaran en la segunda cuota.")

        st.divider()

        # --- TABLA 3: FALLÓ ENTRE 3RA Y 6TA ---
        st.subheader("Seguimiento: Fallaron entre 3ra y 6ta cuota")
        df_sec3 = df_cosechas[df_cosechas['Grupo_Seguimiento'] == 'SECCION_3_FALLO_3RA_PLUS']
        
        if not df_sec3.empty:
            st.markdown(f"**Clientes encontrados:** {len(df_sec3)}")
            st.dataframe(
                df_sec3[columnas_finales],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No hay clientes nuevos con fallas entre la 3ra y 6ta cuota.")

    else:
        st.success("Excelente: No hay créditos desembolsados en los últimos 6 meses con mora actual.")
