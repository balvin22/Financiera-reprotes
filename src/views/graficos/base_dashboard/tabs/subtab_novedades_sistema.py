import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from src.views.graficos.base_dashboard import charts_call_center  

def render(novedades_data):
    """
    Renderiza el contenido visual del sub-tab Novedades del Sistema.
    Muestra gráficos de cobertura y tipificación, y una TABLA DETALLADA DE CARTERA.
    """
    # --- 1. Validación y Carga de Datos ---
    if not novedades_data:
        st.error("No se recibieron datos.")
        return

    if novedades_data.get("error"):
        st.warning(f"⚠️ {novedades_data['error']}")
        if novedades_data.get("df_cartera_call", pd.DataFrame()).empty:
            return

    df_cartera_call = novedades_data.get("df_cartera_call", pd.DataFrame())
    df_compromisos = novedades_data.get("df_compromisos", pd.DataFrame())
    df_detalle_novedades = novedades_data.get("df_detalle", pd.DataFrame())

    st.markdown("### 📋 Análisis de Cobertura y Gestión")

    # --- 2. Sección de Gráficos ---
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 1. Cobertura de Gestión")
        st.caption("Proporción de créditos con gestión vs. sin gestión.")
        if not df_cartera_call.empty:
            fig_dona_gestion = charts_call_center.create_gestion_donut_chart(df_cartera_call)
            if fig_dona_gestion:
                st.plotly_chart(fig_dona_gestion, use_container_width=True)
            else:
                st.warning("Falta columna 'Estado_Gestion'.")
        else:
            st.info("Esperando datos de cartera...")

    with c2:
        st.markdown("#### 2. Tipificación de la Gestión")
        st.caption("Desglose de 'Tipo de Novedad' (Solo gestionados).")
        if not df_cartera_call.empty:
            fig_dona_tipo = charts_call_center.create_tipo_novedad_donut_chart(df_cartera_call)
            if fig_dona_tipo:
                st.plotly_chart(fig_dona_tipo, use_container_width=True)
            else:
                st.info("No hay créditos gestionados para mostrar tipos.")
        else:
            st.info("Esperando datos de cartera...")

    st.divider()

    st.subheader("🤝 Seguimiento de Acuerdos de Pago")
    
    if not df_compromisos.empty:
        # Métricas rápidas
        total_vig = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS VIGENTES']['Cantidad'].sum()
        total_ven = df_compromisos[df_compromisos['Estado_Acuerdo']=='ACUERDOS VENCIDOS']['Cantidad'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Acuerdos", total_vig + total_ven)
        m2.metric("Vigentes (Al día)", total_vig)
        m3.metric("Vencidos", total_ven, delta_color="inverse")
        
        # Gráfico de Barras Apiladas
        fig_stack = charts_call_center.create_compromisos_stacked_bar_chart(df_compromisos)
        if fig_stack:
            st.plotly_chart(fig_stack, use_container_width=True)
    else:
        st.info("No se encontraron 'Compromisos de Pago' con fechas válidas en el mes actual.")

    # --- 3. SECCIÓN DE TABLA
    st.subheader("🔍 Detalle de Cartera y Gestión")
    
    if not df_cartera_call.empty:
        
        # --- PREPARACIÓN DE DATOS PARA LA TABLA ---
        # Unificar columna de Call Center para el filtro (Zona o Apoyo)
        # Si 'Zona' es CL1-CL4 usamos Zona, si no usamos Call_Center_Apoyo
        def obtener_cc_visual(row):
            zona = str(row.get('Zona', '')).strip()
            if zona in ['CL1', 'CL2', 'CL3', 'CL4']:
                return zona
            return str(row.get('Call_Center_Apoyo', row.get('Zona', ''))).strip()

        df_view = df_cartera_call.copy()
        df_view['Call_Center_Visual'] = df_view.apply(obtener_cc_visual, axis=1)
        
        # Asegurar columnas clave
        if 'Estado_Gestion' not in df_view.columns: df_view['Estado_Gestion'] = 'SIN DATO'
        if 'Tipo_Novedad' not in df_view.columns: df_view['Tipo_Novedad'] = ''
        if 'Novedad' not in df_view.columns: df_view['Novedad'] = ''

        # --- FILTROS ---
        col_f1, col_f2, col_f3 = st.columns(3)
        
        # A. Filtro Call Center
        opciones_cc = ['TODOS'] + sorted(list(df_view['Call_Center_Visual'].unique()))
        sel_cc = col_f1.selectbox("Filtrar Call Center:", opciones_cc)
        
        # B. [NUEVO] Filtro Estado Gestión
        opciones_gestion = ['TODOS'] + sorted(list(df_view['Estado_Gestion'].unique()))
        sel_gestion = col_f2.selectbox("Filtrar Estado Gestión:", opciones_gestion)
        
        # C. Filtro Tipo Novedad
        # Solo mostramos tipos que existen en la data filtrada para limpiar la vista
        opciones_tipo = ['TODOS'] + sorted(list(df_view['Tipo_Novedad'].astype(str).unique()))
        sel_tipo = col_f3.selectbox("Filtrar Tipo Novedad:", opciones_tipo)

        # --- APLICACIÓN DE FILTROS ---
        if sel_cc != 'TODOS':
            df_view = df_view[df_view['Call_Center_Visual'] == sel_cc]
        
        if sel_gestion != 'TODOS':
            df_view = df_view[df_view['Estado_Gestion'] == sel_gestion]
            
        if sel_tipo != 'TODOS':
            df_view = df_view[df_view['Tipo_Novedad'].astype(str) == sel_tipo]

        # --- VISUALIZACIÓN ---
        # Definimos columnas útiles para el análisis
        columnas_deseadas = [
            'Call_Center_Visual', 'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular',
            'Estado_Gestion', 'Tipo_Novedad', 'Novedad', 
            'Fecha_Cuota_Vigente', 'Dias_Atraso_Final', 'Total_Recaudo'
        ]
        # Intersección para evitar errores si falta alguna columna
        cols_finales = [c for c in columnas_deseadas if c in df_view.columns]

        st.dataframe(
            df_view[cols_finales],
            use_container_width=True, 
            hide_index=True
        )
        
        st.caption(f"Mostrando {len(df_view)} créditos.")
        
    else:
        st.warning("No hay datos de cartera disponibles.")