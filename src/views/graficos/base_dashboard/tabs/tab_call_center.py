import streamlit as st
import pandas as pd
from datetime import date
from src.views.graficos.base_dashboard import charts_call_center

try:
    from . import subtab_llamadas
    from . import subtab_mensajeria
    IMPORT_SUCCESS = True
except ImportError:
    try:
        import subtab_llamadas
        import subtab_mensajeria
        IMPORT_SUCCESS = True
    except ImportError as e:
        st.error(f"Error crítico al importar sub-tabs: {e}")
        IMPORT_SUCCESS = False


def render(tab6_data, charts_resultados):
    """
    Renderiza el contenido del Tab 6: Call Centers.
    La tabla de detalle solo muestra créditos asociados a Call Centers.
    Al final se añaden tabs con análisis adicionales.
    """
    st.header("Rendimiento de Call Centers")
    if not tab6_data or not any(key in tab6_data for key in ["reporte_raw", "rodamiento_data", "cartera_detallada_call_center"]):
        st.warning("No hay datos de Call Center para mostrar con los filtros seleccionados.")
        return

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
    

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cumplimiento de Call Center")
        fig_bar = charts_call_center.create_cumplimiento_bar_chart(df_raw)
        if fig_bar:
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos para el gráfico de cumplimiento.")

    with col2:
        st.subheader("Rodamientos en Call Centers")
        fig_pie = charts_call_center.create_rodamiento_pie_chart(df_rodamiento_count)
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos para el gráfico de rodamientos.")

    st.markdown("---")

    if not df_raw.empty:
        st.subheader("Metas por Call Center")
        expected_compliance, start_date, end_date = charts_resultados.calculate_expected_compliance()
        st.info(f"**Meta de cumplimiento para hoy ({date.today().strftime('%d/%m/%Y')}): {expected_compliance:.2%}** | "
                f"Periodo: {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}")
        st.markdown("---")
        
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
        col1_m, col2_m, col3_m, col4_m = st.columns(4)
        col1_m.metric("Meta Total", f"${total_meta:,.0f}")
        col2_m.metric("Recaudo Total", f"${total_recaudo:,.0f}")
        col3_m.metric("Faltante Total", f"${total_meta - total_recaudo:,.0f}")
        col4_m.metric("Cumplimiento Total", f"{(total_recaudo / total_meta) if total_meta > 0 else 0:.2%}")
        st.markdown("---")

    st.header("Detalle de Créditos por Call Center")
    if df_cartera_detalle.empty:
        st.warning("No se encontraron créditos asociados a Call Centers con los filtros principales seleccionados.")
    else:
        st.write("#### Filtros de Búsqueda")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        # Las opciones para los filtros se derivan del DataFrame ya filtrado
        rodamiento_options = sorted(df_cartera_detalle['Rodamiento'].unique())
        gestion_options = sorted(df_cartera_detalle['Estado_Gestion'].unique())
        pago_options = sorted(df_cartera_detalle['Estado_Pago'].unique())
        novedad_options = sorted(df_cartera_detalle['Tipo_Novedad'].unique())
        
        # --- FILTROS (Popovers) ---
        with col_f1:
            st.write("Filtrar por rodamiento:")
            with st.popover("Seleccionar Rodamientos...", use_container_width=True):
                if st.button("Todos", use_container_width=True, key="select_all_rodamiento_det"):
                    for opt in rodamiento_options: st.session_state[f"rod_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_rodamiento_det"):
                    for opt in rodamiento_options: st.session_state[f"rod_det_{opt}"] = False
                st.markdown("---")
                for opt in rodamiento_options:
                    if f"rod_det_{opt}" not in st.session_state: st.session_state[f"rod_det_{opt}"] = True
                    st.checkbox(opt, key=f"rod_det_{opt}")
            selected_rodamientos = [opt for opt in rodamiento_options if st.session_state.get(f"rod_det_{opt}", True)]
            st.caption(f"{len(selected_rodamientos)} de {len(rodamiento_options)} seleccionados.")

        with col_f2:
            st.write("Filtrar por gestión:")
            with st.popover("Seleccionar Estados...", use_container_width=True):
                if st.button("Todos", use_container_width=True, key="select_all_gestion_det"):
                    for opt in gestion_options: st.session_state[f"gestion_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_gestion_det"):
                    for opt in gestion_options: st.session_state[f"gestion_det_{opt}"] = False
                st.markdown("---")
                for opt in gestion_options:
                    if f"gestion_det_{opt}" not in st.session_state: st.session_state[f"gestion_det_{opt}"] = True
                    st.checkbox(opt, key=f"gestion_det_{opt}")
            selected_gestiones = [opt for opt in gestion_options if st.session_state.get(f"gestion_det_{opt}", True)]
            st.caption(f"{len(selected_gestiones)} de {len(gestion_options)} seleccionados.")

        with col_f3:
            st.write("Filtrar por pago:")
            with st.popover("Seleccionar Estados...", use_container_width=True):
                if st.button("Todos", use_container_width=True, key="select_all_pago_det"):
                    for opt in pago_options: st.session_state[f"pago_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_pago_det"):
                    for opt in pago_options: st.session_state[f"pago_det_{opt}"] = False
                st.markdown("---")
                for opt in pago_options:
                    if f"pago_det_{opt}" not in st.session_state: st.session_state[f"pago_det_{opt}"] = True
                    st.checkbox(opt, key=f"pago_det_{opt}")
            selected_pagos = [opt for opt in pago_options if st.session_state.get(f"pago_det_{opt}", True)]
            st.caption(f"{len(selected_pagos)} de {len(pago_options)} seleccionados.")

        with col_f4:
            st.write("Filtrar por novedad:")
            with st.popover("Seleccionar Novedades...", use_container_width=True):
                if st.button("Todos", use_container_width=True, key="select_all_novedad_det"):
                    for opt in novedad_options: st.session_state[f"novedad_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_novedad_det"):
                    for opt in novedad_options: st.session_state[f"novedad_det_{opt}"] = False
                st.markdown("---")
                for opt in novedad_options:
                    if f"novedad_det_{opt}" not in st.session_state: st.session_state[f"novedad_det_{opt}"] = True
                    st.checkbox(opt, key=f"novedad_det_{opt}")
            selected_novedades = [opt for opt in novedad_options if st.session_state.get(f"novedad_det_{opt}", True)]
            st.caption(f"{len(selected_novedades)} de {len(novedad_options)} seleccionados.")
        
        # Aplicar filtros al DataFrame de detalle
        df_tabla = df_cartera_detalle.copy()
        if selected_rodamientos: df_tabla = df_tabla[df_tabla['Rodamiento'].isin(selected_rodamientos)]
        if selected_gestiones: df_tabla = df_tabla[df_tabla['Estado_Gestion'].isin(selected_gestiones)]
        if selected_pagos: df_tabla = df_tabla[df_tabla['Estado_Pago'].isin(selected_pagos)]
        if selected_novedades: df_tabla = df_tabla[df_tabla['Tipo_Novedad'].isin(selected_novedades)]

        todas_las_columnas_posibles = [
            'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 'Gestor', 'Zona','Telefono_Gestor', 
            'Codeudor1', 'Nombre_Codeudor1', 'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2', 'Telefono_Codeudor2',
            'Dias_Atraso_Final', 'Total_Recaudo', 'Nombre_Producto', 'Total_Cuotas', 'Valor_Vencido','Rodamiento','Valor_Cuota_Vigente',
            'Rodamiento_Cartera','Estado_Pago', 'Estado_Gestion','Tipo_Novedad','Novedad','Franja_Meta','Fecha_Cuota_Vigente',
            'Valor_Cuota','Cuotas_Pagadas','Cobrador','Telefono_Cobrador'
        ]
        columnas_disponibles = [col for col in todas_las_columnas_posibles if col in df_tabla.columns]
        
        st.markdown("---")
        columnas_seleccionadas = st.multiselect(
            "Selecciona las columnas a mostrar en la tabla:",
            options=columnas_disponibles,
            default=['Credito', 'Cedula_Cliente', 'Nombre_Cliente','Celular','Franja_Meta','Dias_Atraso_Final', 'Rodamiento', 'Valor_Vencido',
                     'Total_Recaudo','Fecha_Cuota_Vigente','Valor_Cuota_Vigente','Valor_Cuota'],
            key="multiselect_detalle_call"
        )
        
        st.info(f"Mostrando {len(df_tabla)} de {len(df_cartera_detalle)} créditos que coinciden con los filtros")
        if not columnas_seleccionadas:
            st.warning("Por favor, selecciona al menos una columna para mostrar en la tabla.")
        elif not df_tabla.empty:
            st.data_editor(
                df_tabla[columnas_seleccionadas],
                use_container_width=True,
                hide_index=True,
                disabled=True,
                key="editor_detalle_call_center"
            )
        else:
            st.warning("No se encontraron créditos que coincidan con la selección de filtros.")
    st.markdown("---") 

    if IMPORT_SUCCESS:
        st.header("Llamadas y Mensajeria")
        tab_llamadas, tab_mensajeria = st.tabs([
            "📞 Llamadas Call Center", 
            "💬 Mensajería Call Center"
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
            subtab_mensajeria.render(
                df_mensajeria=df_mensajeria_filtrada,
                df_cartera_detalle=df_cartera_detalle,
                df_funnel_mensajeria=df_funnel_mensajeria,
                df_efectividad_mensajeria=df_efectividad_mensajeria
            )
    else:
        st.error("No se pudieron cargar los módulos de análisis adicional (sub-tabs).")