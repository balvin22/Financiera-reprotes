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


# MODIFICACIÓN: Añadir 'alerts' como tercer argumento
def render(tab6_data, charts_resultados, alerts):
    """
    Renderiza el contenido del Tab 6: Call Centers.
    Ahora recibe un diccionario de alertas para mostrar dentro de los sub-tabs.
    """
    
    # --- EXTRAER ALERTA DE NEGOCIO DEL DICCIONARIO DE DATOS ---
    novedades_alert = tab6_data.pop("novedades_alert", None)
    
    if novedades_alert:
        alerts['novedades_error'] = novedades_alert
        
    # Asignación de datos (usando .get para seguridad)
    # ----------------------------------------------------------------------------------
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
    # ----------------------------------------------------------------------------------

    # --- RENDERIZADO PRINCIPAL DEL TAB 6 ---
    st.header("Rendimiento de Call Centers")
    
    if not tab6_data or not any(key in tab6_data for key in ["reporte_raw", "rodamiento_data", "cartera_detallada_call_center"]):
        st.warning("No hay datos de Call Center para mostrar con los filtros seleccionados.")
        return

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
        # ... (Lógica de filtros de la tabla de detalle se mantiene igual) ...
        # Por brevedad, asumo que el código de los filtros y la tabla (st.data_editor) sigue aquí igual que en tu archivo original.
        # ...
        pass 
        
        # Re-inserto la lógica de visualización de la tabla para que el archivo sea funcional al copiar y pegar:
        st.write("#### Filtros de Búsqueda")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        rodamiento_options = sorted(df_cartera_detalle['Rodamiento'].unique())
        gestion_options = sorted(df_cartera_detalle['Estado_Gestion'].unique())
        pago_options = sorted(df_cartera_detalle['Estado_Pago'].unique())
        novedad_options = sorted(df_cartera_detalle['Tipo_Novedad'].unique())
        
        with col_f1:
            with st.popover("Rodamientos...", use_container_width=True):
                for opt in rodamiento_options:
                    if f"rod_det_{opt}" not in st.session_state: st.session_state[f"rod_det_{opt}"] = True
                    st.checkbox(opt, key=f"rod_det_{opt}")
                selected_rodamientos = [opt for opt in rodamiento_options if st.session_state.get(f"rod_det_{opt}", True)]
        with col_f2:
            with st.popover("Gestión...", use_container_width=True):
                for opt in gestion_options:
                    if f"gestion_det_{opt}" not in st.session_state: st.session_state[f"gestion_det_{opt}"] = True
                    st.checkbox(opt, key=f"gestion_det_{opt}")
                selected_gestiones = [opt for opt in gestion_options if st.session_state.get(f"gestion_det_{opt}", True)]
        with col_f3:
            with st.popover("Pagos...", use_container_width=True):
                for opt in pago_options:
                    if f"pago_det_{opt}" not in st.session_state: st.session_state[f"pago_det_{opt}"] = True
                    st.checkbox(opt, key=f"pago_det_{opt}")
                selected_pagos = [opt for opt in pago_options if st.session_state.get(f"pago_det_{opt}", True)]
        with col_f4:
            with st.popover("Novedades...", use_container_width=True):
                for opt in novedad_options:
                    if f"novedad_det_{opt}" not in st.session_state: st.session_state[f"novedad_det_{opt}"] = True
                    st.checkbox(opt, key=f"novedad_det_{opt}")
                selected_novedades = [opt for opt in novedad_options if st.session_state.get(f"novedad_det_{opt}", True)]

        df_tabla = df_cartera_detalle.copy()
        if selected_rodamientos: df_tabla = df_tabla[df_tabla['Rodamiento'].isin(selected_rodamientos)]
        if selected_gestiones: df_tabla = df_tabla[df_tabla['Estado_Gestion'].isin(selected_gestiones)]
        if selected_pagos: df_tabla = df_tabla[df_tabla['Estado_Pago'].isin(selected_pagos)]
        if selected_novedades: df_tabla = df_tabla[df_tabla['Tipo_Novedad'].isin(selected_novedades)]

        todas_las_columnas = ['Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 'Franja_Meta', 'Dias_Atraso_Final', 'Rodamiento', 'Valor_Vencido', 'Total_Recaudo', 'Fecha_Cuota_Vigente', 'Tipo_Novedad', 'Novedad']
        cols_disponibles = [c for c in todas_las_columnas if c in df_tabla.columns]
        
        st.markdown("---")
        if not df_tabla.empty:
            st.data_editor(df_tabla[cols_disponibles], use_container_width=True, hide_index=True, disabled=True, key="editor_detalle_call")
        else:
            st.warning("No hay datos con estos filtros.")

    st.markdown("---") 

    if IMPORT_SUCCESS:
        st.header("Llamadas, Mensajería y Novedades")
        tab_llamadas, tab_mensajeria, tab_novedades = st.tabs([
            "📞 Llamadas Call Center", 
            "💬 Mensajería Call Center",
            "📋 Novedades del Sistema"
        ])
        
        # --- MOSTRAR ALERTAS EN SUS SUB-TABS RESPECTIVOS ---
        
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

            # 3. LLAMAR AL RENDER
            subtab_novedades_sistema.render(novedades_data_package)
            
    else:
        st.error("No se pudieron cargar los módulos de análisis adicional (sub-tabs).")