import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import numpy as np

def render(tab6_data, charts_resultados):
    """
    Renderiza el contenido del Tab 6: Call Centers, incluyendo gráficos,
    tabla de resumen de Call Centers y la nueva tabla de Detalle de Créditos por Call.
    """
    st.header("Análisis de Rendimiento de Call Centers")

    if not tab6_data or not any(key in tab6_data for key in ["reporte_raw", "rodamiento_data", "cartera_detallada_call_center"]):
        st.warning("No hay datos de Call Center para mostrar con los filtros seleccionados.")
        return

    # Extraemos los dataframes del diccionario
    df_raw = tab6_data.get("reporte_raw", pd.DataFrame()) # Resumen de Call Centers
    df_rodamiento_count = tab6_data.get("rodamiento_data", pd.DataFrame()) # Conteo de rodamientos para el gráfico de torta
    df_cartera_detalle = tab6_data.get("cartera_detallada_call_center", pd.DataFrame()) # Detalle de créditos
    
    # Aseguramos que el DF de detalle no esté vacío para la tabla de créditos
    if df_cartera_detalle.empty:
        st.warning("El DataFrame de detalle de créditos está vacío.")
        return

    # --- RENDERIZACIÓN DE GRÁFICOS Y RESUMEN (CÓDIGO ANTERIOR) ---
    # ... (Sección de gráficos y resumen de Call Centers) ...
    
    col1, col2 = st.columns(2)
    with col1:
        if not df_raw.empty:
            st.subheader("Cumplimiento de Call Center")
            df_chart = df_raw.sort_values(by='CALL_CENTER', ascending=False).copy()
            df_chart['texto_cumplimiento'] = (df_chart['Cumplimiento'] * 100).map('{:.2f}%'.format).str.replace('.', ',')
            
            fig_bar = px.bar(
                df_chart, x='Cumplimiento', y='CALL_CENTER', orientation='h', text='texto_cumplimiento',
                labels={'CALL_CENTER': 'Call Center', 'Cumplimiento': 'Porcentaje de Cumplimiento'}
            )
            fig_bar.update_layout(xaxis_tickformat='.0%', yaxis_title=None, margin=dict(l=20, r=20, t=40, b=20))
            fig_bar.update_traces(textposition='auto', marker_color='#1f77b4')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos para el gráfico de cumplimiento.")

    # --- Gráfico de Torta en la Columna 2 ---
    with col2:
        if not df_rodamiento_count.empty:
            st.subheader("Rodamientos en Call Centers")
            fig_pie = px.pie(
                df_rodamiento_count,
                names='Rodamiento',
                values='count',
            )
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent'
            )
            fig_pie.update_layout(
                showlegend=True,
                legend_title_text='Rodamiento', 
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos para el gráfico de rodamientos.")

    st.markdown("---")
    
    # --- RENDERIZACIÓN DE LA TABLA DE DETALLE DE CALL CENTERS (RESUMEN) ---
    if not df_raw.empty:
        st.subheader("Tabla de Detalle de Call Centers")
        # --- Métrica de Cumplimiento Diaria ---
        expected_compliance, start_date, end_date = charts_resultados.calculate_expected_compliance()
        st.info(f"**Meta de cumplimiento para hoy ({date.today().strftime('%d/%m/%Y')}): {expected_compliance:.2%}** | "
                f"Periodo: {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}")
        st.markdown("---")
        
        # --- Totales Generales ---
        st.subheader("Totales Generales de Call Centers")
        total_meta = df_raw['META_$'].sum()
        total_recaudo = df_raw['Recaudo_Meta'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Meta Total", f"${total_meta:,.0f}")
        col2.metric("Recaudo Total", f"${total_recaudo:,.0f}")
        col3.metric("Faltante Total", f"${total_meta - total_recaudo:,.0f}")
        col4.metric("Cumplimiento Total", f"{(total_recaudo / total_meta) if total_meta > 0 else 0:.2%}")
        
        st.markdown("---")
        
        # --- Tabla de Resumen ---
        df_styled = df_raw.copy()
        df_styled = df_styled.rename(columns={
            'META_$': 'Meta ($)', 'Recaudo_Meta': 'Recaudo ($)', 'Cumplimiento': 'Cumplimiento (%)',
            'NOMBRE': 'Nombre', 'Faltante': 'Faltante ($)'
        })
        column_order = ['CALL_CENTER', 'Nombre', 'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)']
        df_styled = df_styled[column_order]
        styled_df = df_styled.style.map(
            lambda x: charts_resultados.style_cumplimiento_bar(x, expected_compliance),
            subset=['Cumplimiento (%)']
        ).format({
            'Meta ($)': '${:,.0f}', 'Recaudo ($)': '${:,.0f}', 'Faltante ($)': '${:,.0f}', 
            'Cumplimiento (%)': '{:.2%}'
        }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
            {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
        ])
        
        html_table = styled_df.to_html()

        if len(df_styled) > 7:
            st.markdown(
                f'<div style="width: 100%; max-height: 350px; overflow-y: auto;">{html_table}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(html_table, unsafe_allow_html=True)    
    st.markdown("---")
    
    st.header("Detalle de Créditos por Call Center")
    # df_cartera_detalle contiene el detalle de créditos para todos los Call Centers seleccionados
    if not df_cartera_detalle.empty:
        
        st.write("#### Filtros de Búsqueda")
        # Aumentamos el número de columnas para incluir el nuevo filtro
        col_f1, col_f2, col_f3, col_f4 = st.columns(4) 
        
        # --- PREPARACIÓN DE OPCIONES DE FILTRO ---
        # Si el conteo de rodamientos existe, lo usamos. Sino, lo calculamos.
        if df_rodamiento_count.empty:
             agg_rodamiento = df_cartera_detalle.groupby('Rodamiento').size().reset_index(name='count')
        else:
             agg_rodamiento = df_rodamiento_count
        
        rodamiento_options = sorted(agg_rodamiento['Rodamiento'].unique()) if 'Rodamiento' in agg_rodamiento.columns else []
        gestion_options = ['CON GESTIÓN', 'SIN GESTIÓN']
        pago_options = ['PAGO', 'SIN PAGO']
        novedad_options = sorted(df_cartera_detalle['Tipo_Novedad'].unique()) if 'Tipo_Novedad' in df_cartera_detalle.columns else []
        
        # --- FILTRO 1: Rodamiento (Popover) ---
        with col_f1:
            st.write("Filtrar por rodamiento:")
            with st.popover("Seleccionar Rodamientos...", use_container_width=True):
                # Botones de selección rápida (manejo de estado)
                if st.button("Todos", use_container_width=True, key="select_all_rodamiento_det"):
                    for opt in rodamiento_options: st.session_state[f"rod_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_rodamiento_det"):
                    for opt in rodamiento_options: st.session_state[f"rod_det_{opt}"] = False
                st.markdown("---")
                
                for opt in rodamiento_options:
                    if f"rod_det_{opt}" not in st.session_state:
                        st.session_state[f"rod_det_{opt}"] = True
                    st.checkbox(opt, key=f"rod_det_{opt}")
            
            selected_rodamientos = [opt for opt in rodamiento_options if st.session_state.get(f"rod_det_{opt}", True)]
            st.caption(f"{len(selected_rodamientos)} de {len(rodamiento_options)} seleccionados.")

        # --- FILTRO 2: Estado de Gestión (Popover) ---
        with col_f2:
            st.write("Filtrar por gestión:")
            with st.popover("Seleccionar Estados...", use_container_width=True):
                if st.button("Todos", use_container_width=True, key="select_all_gestion_det"):
                    for opt in gestion_options: st.session_state[f"gestion_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_gestion_det"):
                    for opt in gestion_options: st.session_state[f"gestion_det_{opt}"] = False
                st.markdown("---")
                for opt in gestion_options:
                    if f"gestion_det_{opt}" not in st.session_state:
                        st.session_state[f"gestion_det_{opt}"] = True
                    st.checkbox(opt, key=f"gestion_det_{opt}")

            selected_gestiones = [opt for opt in gestion_options if st.session_state.get(f"gestion_det_{opt}", True)]
            st.caption(f"{len(selected_gestiones)} de {len(gestion_options)} seleccionados.")

        # --- FILTRO 3: Estado de Pago (Popover) ---
        with col_f3:
            st.write("Filtrar por pago:")
            with st.popover("Seleccionar Estados...", use_container_width=True):
                if st.button("Todos", use_container_width=True, key="select_all_pago_det"):
                    for opt in pago_options: st.session_state[f"pago_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_pago_det"):
                    for opt in pago_options: st.session_state[f"pago_det_{opt}"] = False
                st.markdown("---")
                for opt in pago_options:
                    if f"pago_det_{opt}" not in st.session_state:
                        st.session_state[f"pago_det_{opt}"] = True
                    st.checkbox(opt, key=f"pago_det_{opt}")

            selected_pagos = [opt for opt in pago_options if st.session_state.get(f"pago_det_{opt}", True)]
            st.caption(f"{len(selected_pagos)} de {len(pago_options)} seleccionados.")
            
        # --- FILTRO 4: Tipo de Novedad (NUEVO Popover) ---
        with col_f4:
            st.write("Filtrar por novedad:")
            with st.popover("Seleccionar Novedades...", use_container_width=True):
                if st.button("Todos", use_container_width=True, key="select_all_novedad_det"):
                    for opt in novedad_options: st.session_state[f"novedad_det_{opt}"] = True
                if st.button("Ninguno", use_container_width=True, key="deselect_all_novedad_det"):
                    for opt in novedad_options: st.session_state[f"novedad_det_{opt}"] = False
                st.markdown("---")
                for opt in novedad_options:
                    if f"novedad_det_{opt}" not in st.session_state:
                        st.session_state[f"novedad_det_{opt}"] = True
                    st.checkbox(opt, key=f"novedad_det_{opt}")

            selected_novedades = [opt for opt in novedad_options if st.session_state.get(f"novedad_det_{opt}", True)]
            st.caption(f"{len(selected_novedades)} de {len(novedad_options)} seleccionados.")

        # --- Lógica para aplicar los filtros a la tabla ---
        df_tabla = df_cartera_detalle.copy() 

        # Aplicamos cada filtro si hay selecciones
        if selected_rodamientos:
            df_tabla = df_tabla[df_tabla['Rodamiento'].isin(selected_rodamientos)]
        
        if selected_gestiones:
            # Asumo que la columna de gestión se llama 'Estado_Gestion' o similar,
            # debes asegurarte del nombre exacto en el DataFrame.
            if 'Estado_Gestion' in df_tabla.columns:
                df_tabla = df_tabla[df_tabla['Estado_Gestion'].isin(selected_gestiones)]
        
        if selected_pagos:
             # Asumo que la columna de pago se llama 'Estado_Pago' o similar
            if 'Estado_Pago' in df_tabla.columns:
                df_tabla = df_tabla[df_tabla['Estado_Pago'].isin(selected_pagos)]

        if selected_novedades:
            if 'Tipo_Novedad' in df_tabla.columns:
                df_tabla = df_tabla[df_tabla['Tipo_Novedad'].isin(selected_novedades)]
                
        # --- Selección de Columnas (Multiselect) ---
        todas_las_columnas_posibles = [
            'Empresa', 'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Celular', 
            'Nombre_Ciudad', 'Zona', 'Codeudor1', 'Nombre_Codeudor1', 'Telefono_Codeudor1','Codeudor2', 'Nombre_Codeudor2', 
            'Telefono_Codeudor2','Dias_Atraso_Final', 'Total_Recaudo', 'Meta_Intereses', 'Meta_Saldo', 'Valor_Vencido','Rodamiento',
            'Rodamiento_Cartera','Estado_Pago', 'Estado_Gestion', 'Empresa', 'Meta_$', 'Tipo_Novedad' # Añadida Tipo_Novedad
        ]
        columnas_disponibles = [col for col in todas_las_columnas_posibles if col in df_tabla.columns]
        
        st.markdown("---")
        columnas_seleccionadas = st.multiselect(
            "Selecciona las columnas a mostrar en la tabla:",
            options=columnas_disponibles,
            default=['Credito', 'Cedula_Cliente', 'Nombre_Cliente','Celular','Rodamiento','Tipo_Novedad', 'Meta_Saldo', 'Valor_Vencido'],
            key="multiselect_detalle_call"
        )
        
        # --- Visualización de la Tabla ---
        st.info(f"Mostrando {len(df_tabla)} créditos que coinciden con los filtros")
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
            st.warning("No se encontraron créditos que coincidan con la selección.")
    
    st.markdown("---")