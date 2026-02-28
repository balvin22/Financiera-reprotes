import streamlit as st
import pandas as pd
from datetime import date
from src.views.graficos.base_dashboard import charts_call_center

try:
    from . import subtab_llamadas
    from . import subtab_mensajeria
    from . import subtab_novedades_sistema
    IMPORT_SUCCESS = True
except ImportError:
    try:
        import subtab_llamadas
        import subtab_mensajeria
        import subtab_novedades_sistema
        IMPORT_SUCCESS = True
    except ImportError as e:
        st.error(f"Error crítico al importar sub-tabs: {e}")
        IMPORT_SUCCESS = False


def render(tab6_data, charts_resultados, alerts):
    """
    Renderiza el contenido del Tab 6: Call Centers con UX optimizada.
    """
    
    # --- EXTRAER ALERTA DE NEGOCIO ---
    novedades_alert = tab6_data.pop("novedades_alert", None)
    if novedades_alert:
        alerts['novedades_error'] = novedades_alert
        
    # Asignación de datos
    df_raw = tab6_data.get("reporte_raw", pd.DataFrame())
    df_rodamiento_count = tab6_data.get("rodamiento_data", pd.DataFrame())
    df_cartera_detalle = tab6_data.get("cartera_detallada_call_center", pd.DataFrame())
    df_llamadas_filtradas = tab6_data.get("df_llamadas_filtrada", pd.DataFrame())
    df_mensajeria_filtrada = tab6_data.get("df_mensajeria_filtrada", pd.DataFrame())
    llamadas_stats = tab6_data.get("llamadas_stats", {})
    df_grafico_llamadas = tab6_data.get("df_grafico_llamadas", pd.DataFrame())
    df_efectividad_call = tab6_data.get("df_efectividad_call", pd.DataFrame())
    df_llamadas_por_dia = tab6_data.get("df_llamadas_por_dia", pd.DataFrame())
    alerta_umbral = tab6_data.get("alerta_umbral", 0)
    df_funnel_mensajeria = tab6_data.get("df_funnel_mensajeria", pd.DataFrame())
    df_efectividad_mensajeria = tab6_data.get("df_efectividad_mensajeria", pd.DataFrame())

    # --- RENDERIZADO PRINCIPAL ---
    st.header("Rendimiento de Call Centers")
    
    if not tab6_data or not any(key in tab6_data for key in ["reporte_raw", "rodamiento_data", "cartera_detallada_call_center"]):
        st.warning("No hay datos de Call Center para mostrar con los filtros seleccionados.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cumplimiento de Call Center")
        with st.container(border=True):
            fig_bar = charts_call_center.create_cumplimiento_bar_chart(df_raw)
            if fig_bar:
                # Ajuste de márgenes para ganar espacio
                fig_bar.update_layout(margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No hay datos para el gráfico de cumplimiento.")

    with col2:
        st.subheader("Rodamientos en Call Centers")
        with st.container(border=True):
            fig_pie = charts_call_center.create_rodamiento_pie_chart(df_rodamiento_count)
            if fig_pie:
                fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No hay datos para el gráfico de rodamientos.")

    st.markdown("---")

    if not df_raw.empty:
        st.subheader("Metas por Call Center")
        expected_compliance, start_date, end_date = charts_resultados.calculate_expected_compliance()
        
        # Mensaje de meta más compacto
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <b>📅 Meta hoy ({date.today().strftime('%d/%m')}):</b> {expected_compliance:.2%} 
                <span style="color: gray;">(Periodo {start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')})</span>
            </div>
            """, unsafe_allow_html=True
        )
        
        html_table = charts_call_center.create_styled_summary_table(
            df_raw, 
            charts_resultados.style_cumplimiento_bar, 
            expected_compliance
        )
        if len(df_raw) > 7:
            st.markdown(f'<div style="width: 100%; max-height: 350px; overflow-y: auto;">{html_table}</div>', unsafe_allow_html=True)
        else:
            st.markdown(html_table, unsafe_allow_html=True)
        
        # Totales Generales
        total_meta = df_raw['META_$'].sum()
        total_recaudo = df_raw['Recaudo_Meta'].sum()
        
        st.divider()
        col1_m, col2_m, col3_m, col4_m = st.columns(4)
        col1_m.metric("Meta Total", f"${total_meta:,.0f}")
        col2_m.metric("Recaudo Total", f"${total_recaudo:,.0f}")
        col3_m.metric("Faltante Total", f"${total_meta - total_recaudo:,.0f}")
        col4_m.metric("Cumplimiento Total", f"{(total_recaudo / total_meta) if total_meta > 0 else 0:.2%}")
        st.markdown("---")
        
    # SECCIÓN DETALLE DE CRÉDITOS
    st.header("Detalle de Créditos por Call Center")
    if df_cartera_detalle.empty:
        st.warning("No se encontraron créditos asociados a Call Centers.")
    else:
        
        # --- CAMBIO: Expanded=False para limpieza visual inicial ---
        with st.expander("Filtros de Búsqueda (Call Center)", expanded=False):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            # Preparar opciones
            rodamiento_options = sorted(df_cartera_detalle['Rodamiento'].astype(str).unique())
            gestion_options = sorted(df_cartera_detalle['Estado_Gestion'].astype(str).unique())
            pago_options = sorted(df_cartera_detalle['Estado_Pago'].astype(str).unique())
            novedad_options = sorted(df_cartera_detalle['Tipo_Novedad'].astype(str).unique())
            
            # --- FILTRO 1: Rodamientos ---
            with col_f1:
                st.write("**Rodamientos**")
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="all_rod_call"):
                        for opt in rodamiento_options: st.session_state[f"call_rod_{opt}"] = True
                    if st.button("Ninguno", key="none_rod_call"):
                        for opt in rodamiento_options: st.session_state[f"call_rod_{opt}"] = False
                    st.divider()
                    for opt in rodamiento_options:
                        if f"call_rod_{opt}" not in st.session_state: st.session_state[f"call_rod_{opt}"] = True
                        st.checkbox(opt, key=f"call_rod_{opt}")
                selected_rodamientos = [opt for opt in rodamiento_options if st.session_state.get(f"call_rod_{opt}", True)]
                st.caption(f"{len(selected_rodamientos)} seleccionados.")

            # --- FILTRO 2: Gestión ---
            with col_f2:
                st.write("**Gestión**")
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="all_gest_call"):
                        for opt in gestion_options: st.session_state[f"call_gest_{opt}"] = True
                    if st.button("Ninguno", key="none_gest_call"):
                        for opt in gestion_options: st.session_state[f"call_gest_{opt}"] = False
                    st.divider()
                    for opt in gestion_options:
                        if f"call_gest_{opt}" not in st.session_state: st.session_state[f"call_gest_{opt}"] = True
                        st.checkbox(opt, key=f"call_gest_{opt}")
                selected_gestiones = [opt for opt in gestion_options if st.session_state.get(f"call_gest_{opt}", True)]
                st.caption(f"{len(selected_gestiones)} seleccionados.")

            # --- FILTRO 3: Pagos ---
            with col_f3:
                st.write("**Pagos**")
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="all_pago_call"):
                        for opt in pago_options: st.session_state[f"call_pago_{opt}"] = True
                    if st.button("Ninguno", key="none_pago_call"):
                        for opt in pago_options: st.session_state[f"call_pago_{opt}"] = False
                    st.divider()
                    for opt in pago_options:
                        if f"call_pago_{opt}" not in st.session_state: st.session_state[f"call_pago_{opt}"] = True
                        st.checkbox(opt, key=f"call_pago_{opt}")
                selected_pagos = [opt for opt in pago_options if st.session_state.get(f"call_pago_{opt}", True)]
                st.caption(f"{len(selected_pagos)} seleccionados.")

            # --- FILTRO 4: Novedades ---
            with col_f4:
                st.write("**Novedades**")
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="all_nov_call"):
                        for opt in novedad_options: st.session_state[f"call_nov_{opt}"] = True
                    if st.button("Ninguno", key="none_nov_call"):
                        for opt in novedad_options: st.session_state[f"call_nov_{opt}"] = False
                    st.divider()
                    for opt in novedad_options:
                        if f"call_nov_{opt}" not in st.session_state: st.session_state[f"call_nov_{opt}"] = True
                        st.checkbox(opt, key=f"call_nov_{opt}")
                selected_novedades = [opt for opt in novedad_options if st.session_state.get(f"call_nov_{opt}", True)]
                st.caption(f"{len(selected_novedades)} seleccionadas.")

        # --- APLICACIÓN DE FILTROS ---
        df_tabla = df_cartera_detalle.copy()
        
        if selected_rodamientos: 
            df_tabla = df_tabla[df_tabla['Rodamiento'].astype(str).isin(selected_rodamientos)]
        if selected_gestiones: 
            df_tabla = df_tabla[df_tabla['Estado_Gestion'].astype(str).isin(selected_gestiones)]
        if selected_pagos: 
            df_tabla = df_tabla[df_tabla['Estado_Pago'].astype(str).isin(selected_pagos)]
        if selected_novedades: 
            df_tabla = df_tabla[df_tabla['Tipo_Novedad'].astype(str).isin(selected_novedades)]

        # --- SELECTOR DE COLUMNAS OCULTO ---
        todas_las_columnas = [
            'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 
            'Franja_Meta', 'Dias_Atraso_Final', 'Rodamiento', 
            'Valor_Vencido', 'Total_Recaudo', 'Fecha_Cuota_Vigente', 
            'Tipo_Novedad', 'Novedad'
        ]
        cols_disponibles = [c for c in todas_las_columnas if c in df_tabla.columns]
        
        st.markdown(f"**Registros encontrados:** {len(df_tabla)}")

        # --- CAMBIO: Selector dentro de Expander ---
        with st.expander("Personalizar Columnas de la Tabla", expanded=False):
            cols_seleccionadas = st.multiselect(
                "Columnas visibles:",
                options=cols_disponibles,
                default=cols_disponibles, 
                key="multi_cols_call_center",
                label_visibility="collapsed"
            )
        
        # --- TABLA INTERACTIVA ---
        if not df_tabla.empty:
            if cols_seleccionadas:
                st.write("💡 **Tip:** Haz clic en una fila para ver el historial completo de novedades de ese cliente.")
                
                # Reemplazamos st.data_editor por un dataframe interactivo
                event = st.dataframe(
                    df_tabla[cols_seleccionadas], 
                    use_container_width=True, 
                    hide_index=True, 
                    selection_mode="single-row", # Permite seleccionar una fila
                    on_select="rerun",           # Recarga la interfaz al hacer clic
                    key="tabla_detalle_call",
                    height=300
                )
                
                # --- LÓGICA DE DETALLE (SUB-TABLA DE NOVEDADES) ---
                if len(event.selection.rows) > 0:
                    row_idx = event.selection.rows[0]
                    cedula_sel = str(df_tabla.iloc[row_idx]['Cedula_Cliente']).strip()
                    nombre_sel = df_tabla.iloc[row_idx].get('Nombre_Cliente', 'Cliente')
                    
                    with st.container(border=True):
                        st.markdown(f"#### 📝 Historial de Novedades: {nombre_sel}")
                        
                        df_nov_crudas = tab6_data.get("novedades_crudas", pd.DataFrame())
                        if not df_nov_crudas.empty:
                            # Filtramos las novedades asociadas a esa cédula
                            df_nov_cliente = df_nov_crudas[df_nov_crudas['Cedula_Cliente'].astype(str).str.strip() == cedula_sel]
                            
                            if not df_nov_cliente.empty:
                                cols_mostrar = [c for c in ['Fecha_Novedad', 'Tipo_Novedad', 'Novedad', 'Nombre_Usuario', 'Cargo_Usuario'] if c in df_nov_cliente.columns]
                                st.dataframe(df_nov_cliente[cols_mostrar], use_container_width=True, hide_index=True)
                            else:
                                st.info("No hay registro de novedades adicionales para este cliente en el archivo actual.")
                        else:
                            st.info("Archivo de novedades no disponible.")
            else:
                st.warning("Selecciona al menos una columna.")
        else:
            st.warning("No hay datos que coincidan con los filtros seleccionados.")

    st.markdown("---") 

    if IMPORT_SUCCESS:
        st.header("Llamadas, Mensajería y Novedades")
        tab_llamadas, tab_mensajeria, tab_novedades = st.tabs([
            "📞 Llamadas Call Center", 
            "💬 Mensajería Call Center",
            "📋 Novedades del Sistema"
        ])
        
        with tab_llamadas:
            subtab_llamadas.render(
                llamadas_stats=llamadas_stats,
                df_grafico_llamadas=df_grafico_llamadas,
                df_llamadas_filtradas=df_llamadas_filtradas,
                df_efectividad_call=df_efectividad_call,
                df_llamadas_por_dia=df_llamadas_por_dia,
                alerta_umbral=alerta_umbral, 
            )

        with tab_mensajeria:
            if alerts.get('mensajeria_error'):
                st.warning(alerts['mensajeria_error'])
                
            subtab_mensajeria.render(
                df_mensajeria=df_mensajeria_filtrada,
                df_cartera_detalle=df_cartera_detalle,
                df_funnel_mensajeria=df_funnel_mensajeria,
                df_efectividad_mensajeria=df_efectividad_mensajeria
            )
            
        with tab_novedades:
            novedades_error = alerts.get('novedades_error')
            if novedades_error:
                st.info(novedades_error)
            novedades_data_package = {
                "df_detalle": tab6_data.get("df_detalle", tab6_data.get("df_novedades_mapeadas", pd.DataFrame())),
                "df_agg_call": tab6_data.get("df_agg_call", tab6_data.get("df_agg_novedades_por_call", pd.DataFrame())),
                "df_agg_tipo": tab6_data.get("df_agg_tipo", tab6_data.get("df_agg_novedades_por_tipo", pd.DataFrame())),
                "df_compromisos": tab6_data.get("df_compromisos", pd.DataFrame()),
                "kpis": tab6_data.get("kpis", {"total": 0, "sin_asignar": 0, "top_tipo": "N/A"}),
                "error": novedades_error,
                "df_cartera_call": df_cartera_detalle
            }
            subtab_novedades_sistema.render(novedades_data_package)            
    else:
        st.error("No se pudieron cargar los módulos de análisis adicional (sub-tabs).")