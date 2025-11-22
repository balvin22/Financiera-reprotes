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
    df_detalle = novedades_data.get("df_detalle", pd.DataFrame())

    st.markdown("### 📋 Análisis de Cobertura y Gestión")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 1. Cobertura de Gestión")
        if not df_cartera_call.empty:
            fig1 = charts_call_center.create_gestion_donut_chart(df_cartera_call)
            if fig1: st.plotly_chart(fig1, use_container_width=True)
    with c2:
        st.markdown("#### 2. Tipificación")
        if not df_cartera_call.empty:
            fig2 = charts_call_center.create_tipo_novedad_donut_chart(df_cartera_call)
            if fig2: st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.subheader("🤝 Seguimiento de Acuerdos de Pago")
    
    if not df_compromisos.empty:
        # Calcular métricas para las 3 categorías
        total_vig = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS VIGENTES']['Cantidad'].sum()
        total_ven = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS VENCIDOS']['Cantidad'].sum()
        total_sin = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS SIN FECHA']['Cantidad'].sum()
        
        # Mostrar 4 métricas (Total + 3 Categorías)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Acuerdos", int(total_vig + total_ven + total_sin))
        m2.metric("Vigentes", int(total_vig))
        m3.metric("Vencidos", int(total_ven), delta_color="off") # Color neutro
        m4.metric("Sin Fecha / Inválidos", int(total_sin), delta_color="inverse") # Rojo si es alto
        
        fig_stack = charts_call_center.create_compromisos_stacked_bar_chart(df_compromisos)
        if fig_stack: st.plotly_chart(fig_stack, use_container_width=True)
    else:
        st.info("No se encontraron 'Compromisos de Pago'.")

    st.subheader("🔍 Detalle de Cartera y Gestión")
    
    if not df_cartera_call.empty:
        def obtener_cc_visual(row):
            zona = str(row.get('Zona', '')).strip()
            if zona in ['CL1', 'CL2', 'CL3', 'CL4']: return zona
            return str(row.get('Call_Center_Apoyo', row.get('Zona', ''))).strip()

        df_view = df_cartera_call.copy()
        df_view['Call_Center_Visual'] = df_view.apply(obtener_cc_visual, axis=1)
        
        if 'Estado_Gestion' not in df_view.columns: df_view['Estado_Gestion'] = 'SIN DATO'
        if 'Tipo_Novedad' not in df_view.columns: df_view['Tipo_Novedad'] = ''

        col_f1, col_f2, col_f3 = st.columns(3)
        opciones_cc = ['TODOS'] + sorted(list(df_view['Call_Center_Visual'].unique()))
        sel_cc = col_f1.selectbox("Filtrar Call Center:", opciones_cc)
        opciones_gestion = ['TODOS'] + sorted(list(df_view['Estado_Gestion'].unique()))
        sel_gestion = col_f2.selectbox("Filtrar Estado Gestión:", opciones_gestion)
        opciones_tipo = ['TODOS'] + sorted(list(df_view['Tipo_Novedad'].astype(str).unique()))
        sel_tipo = col_f3.selectbox("Filtrar Tipo Novedad:", opciones_tipo)

        if sel_cc != 'TODOS': df_view = df_view[df_view['Call_Center_Visual'] == sel_cc]
        if sel_gestion != 'TODOS': df_view = df_view[df_view['Estado_Gestion'] == sel_gestion]
        if sel_tipo != 'TODOS': df_view = df_view[df_view['Tipo_Novedad'].astype(str) == sel_tipo]

        cols_display = ['Call_Center_Visual', 'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 'Estado_Gestion', 'Tipo_Novedad', 'Novedad', 'Fecha_Cuota_Vigente', 'Dias_Atraso_Final']
        final_cols = [c for c in cols_display if c in df_view.columns]

        st.dataframe(df_view[final_cols].astype(str), use_container_width=True, hide_index=True)
        st.caption(f"Mostrando {len(df_view)} créditos.")
    else:
        st.warning("No hay datos de cartera disponibles.")