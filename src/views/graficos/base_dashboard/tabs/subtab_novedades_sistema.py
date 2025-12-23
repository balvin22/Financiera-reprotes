import streamlit as st
import plotly.express as px
import pandas as pd
from src.views.graficos.base_dashboard import charts_call_center  

def render(novedades_data):
    if not novedades_data:
        st.error("No se recibieron datos.")
        return

    if novedades_data.get("error"):
        st.warning(f"⚠️ {novedades_data['error']}")
        if novedades_data.get("df_cartera_call", pd.DataFrame()).empty:
            return

    df_cartera_call = novedades_data.get("df_cartera_call", pd.DataFrame())
    df_compromisos = novedades_data.get("df_compromisos", pd.DataFrame())
    
    # --- SECCIÓN 1: GRÁFICOS DE COBERTURA ---
    st.markdown("### Análisis de Cobertura y Gestión")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### 1. Cobertura de Gestión")
            if not df_cartera_call.empty:
                fig1 = charts_call_center.create_gestion_donut_chart(df_cartera_call)
                if fig1: 
                    fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Sin datos.")

    with c2:
        with st.container(border=True):
            st.markdown("#### 2. Tipificación")
            if not df_cartera_call.empty:
                fig2 = charts_call_center.create_tipo_novedad_donut_chart(df_cartera_call)
                if fig2: 
                    fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Sin datos.")

    st.divider()

    # --- SECCIÓN 2: ACUERDOS DE PAGO ---
    st.subheader("Seguimiento de Acuerdos de Pago")
    
    if not df_compromisos.empty:
        # Calcular métricas
        total_vig = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS VIGENTES']['Cantidad'].sum()
        total_ven = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS VENCIDOS']['Cantidad'].sum()
        total_sin = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS SIN FECHA']['Cantidad'].sum()
        
        # Tarjetas de métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Acuerdos", int(total_vig + total_ven + total_sin))
        m2.metric("Vigentes", int(total_vig))
        m3.metric("Vencidos", int(total_ven), delta_color="off") 
        m4.metric("Sin Fecha / Inválidos", int(total_sin), delta_color="inverse") 
        
        with st.container(border=True):
            fig_stack = charts_call_center.create_compromisos_stacked_bar_chart(df_compromisos)
            if fig_stack: 
                fig_stack.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_stack, use_container_width=True)
    else:
        st.info("No se encontraron 'Compromisos de Pago'.")

    st.divider()

    # --- SECCIÓN 3: DETALLE DE CARTERA (TABLA) ---
    st.subheader("Detalle de Cartera y Gestión")
    
    if not df_cartera_call.empty:
        # Pre-procesamiento (Lógica original intacta)
        def obtener_cc_visual(row):
            zona = str(row.get('Zona', '')).strip()
            if zona in ['CL1', 'CL2', 'CL3', 'CL4']: return zona
            return str(row.get('Call_Center_Apoyo', row.get('Zona', ''))).strip()

        df_view = df_cartera_call.copy()
        df_view['Call_Center_Visual'] = df_view.apply(obtener_cc_visual, axis=1)
        
        if 'Estado_Gestion' not in df_view.columns: df_view['Estado_Gestion'] = 'SIN DATO'
        if 'Tipo_Novedad' not in df_view.columns: df_view['Tipo_Novedad'] = ''

        # --- CAMBIO: Filtros colapsados (Expanded=False) ---
        with st.expander("Filtros de Detalle (Novedades)", expanded=False):
            col_f1, col_f2, col_f3 = st.columns(3)
            
            # Preparar opciones únicas ordenadas
            opciones_cc = sorted(list(df_view['Call_Center_Visual'].astype(str).unique()))
            opciones_gestion = sorted(list(df_view['Estado_Gestion'].astype(str).unique()))
            opciones_tipo = sorted(list(df_view['Tipo_Novedad'].astype(str).unique()))

            # --- FILTRO 1: Call Center ---
            with col_f1:
                st.write("**Call Center**")
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="all_cc_nov"):
                        for opt in opciones_cc: st.session_state[f"nov_cc_{opt}"] = True
                    if st.button("Ninguno", key="none_cc_nov"):
                        for opt in opciones_cc: st.session_state[f"nov_cc_{opt}"] = False
                    st.divider()
                    for opt in opciones_cc:
                        if f"nov_cc_{opt}" not in st.session_state: st.session_state[f"nov_cc_{opt}"] = True
                        st.checkbox(opt, key=f"nov_cc_{opt}")
                
                selected_cc = [opt for opt in opciones_cc if st.session_state.get(f"nov_cc_{opt}", True)]
                st.caption(f"{len(selected_cc)} seleccionados.")

            # --- FILTRO 2: Estado Gestión ---
            with col_f2:
                st.write("**Estado Gestión**")
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="all_gest_nov"):
                        for opt in opciones_gestion: st.session_state[f"nov_gest_{opt}"] = True
                    if st.button("Ninguno", key="none_gest_nov"):
                        for opt in opciones_gestion: st.session_state[f"nov_gest_{opt}"] = False
                    st.divider()
                    for opt in opciones_gestion:
                        if f"nov_gest_{opt}" not in st.session_state: st.session_state[f"nov_gest_{opt}"] = True
                        st.checkbox(opt, key=f"nov_gest_{opt}")
                
                selected_gestion = [opt for opt in opciones_gestion if st.session_state.get(f"nov_gest_{opt}", True)]
                st.caption(f"{len(selected_gestion)} seleccionados.")

            # --- FILTRO 3: Tipo Novedad ---
            with col_f3:
                st.write("**Tipo Novedad**")
                with st.popover("Seleccionar...", use_container_width=True):
                    if st.button("Todos", key="all_tipo_nov"):
                        for opt in opciones_tipo: st.session_state[f"nov_tipo_{opt}"] = True
                    if st.button("Ninguno", key="none_tipo_nov"):
                        for opt in opciones_tipo: st.session_state[f"nov_tipo_{opt}"] = False
                    st.divider()
                    for opt in opciones_tipo:
                        if f"nov_tipo_{opt}" not in st.session_state: st.session_state[f"nov_tipo_{opt}"] = True
                        st.checkbox(opt, key=f"nov_tipo_{opt}")
                
                selected_tipo = [opt for opt in opciones_tipo if st.session_state.get(f"nov_tipo_{opt}", True)]
                st.caption(f"{len(selected_tipo)} seleccionados.")

        # --- APLICACIÓN DE FILTROS ---
        if selected_cc:
            df_view = df_view[df_view['Call_Center_Visual'].astype(str).isin(selected_cc)]
        if selected_gestion:
            df_view = df_view[df_view['Estado_Gestion'].astype(str).isin(selected_gestion)]
        if selected_tipo:
            df_view = df_view[df_view['Tipo_Novedad'].astype(str).isin(selected_tipo)]

        # --- SELECTOR DE COLUMNAS OCULTO ---
        cols_default_display = [
            'Call_Center_Visual', 'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 
            'Celular', 'Estado_Gestion', 'Tipo_Novedad', 'Novedad', 
            'Fecha_Cuota_Vigente', 'Dias_Atraso_Final'
        ]
        cols_totales = list(df_view.columns)
        cols_default_validas = [c for c in cols_default_display if c in cols_totales]

        st.markdown(f"**Registros encontrados:** {len(df_view)}")

        # --- CAMBIO: Selector en Expander ---
        with st.expander("Personalizar Columnas de la Tabla", expanded=False):
            cols_seleccionadas = st.multiselect(
                "Columnas visibles:",
                options=cols_totales,
                default=cols_default_validas,
                key="multi_cols_novedades",
                label_visibility="collapsed"
            )

        if not df_view.empty:
            if cols_seleccionadas:
                st.data_editor(
                    df_view[cols_seleccionadas], 
                    use_container_width=True, 
                    hide_index=True,
                    disabled=True,
                    height=400
                )
            else:
                st.warning("Selecciona al menos una columna.")
        else:
            st.warning("No hay datos que coincidan con los filtros seleccionados.")   
    else:
        st.warning("No hay datos de cartera disponibles.")