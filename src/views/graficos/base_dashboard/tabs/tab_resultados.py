import streamlit as st
import charts_resultados 
from datetime import date

def render(tab3_data): 
    """
    Renderiza el contenido de la pestaña "Resultados".
    Ahora maneja un diccionario con resultados por Zona y por Cobrador.
    """ 
    if tab3_data is None or not isinstance(tab3_data, dict):
        st.warning("No se encontraron datos de resultados para los filtros globales seleccionados.")
        return

    df_resultados_zona = tab3_data.get("resultados_zona", None)
    df_resultados_cobrador = tab3_data.get("resultados_cobrador", None)

    if df_resultados_zona is None or df_resultados_zona.empty:
        st.warning("No se encontraron datos de resultados de ZONA para los filtros globales seleccionados.")
        # Continuar para revisar la tabla de Cobrador
    
    # --- FILTRO Y GRÁFICOS DE ZONAS (Lógica existente) ---
    st.header("Resultados de Cumplimiento por Zona y Franja")

    if df_resultados_zona is not None and not df_resultados_zona.empty:
        
        # 1. Filtro de zonas
        zonas_disponibles = sorted(df_resultados_zona['Zona'].unique())
        with st.popover("Selecciona una o más Zonas...", use_container_width=False):
            if st.button("Seleccionar Todas", key="select_all_zonas"):
                for zona in zonas_disponibles: st.session_state[f"zona_{zona}"] = True
            if st.button("Deseleccionar Todas", key="deselect_all_zonas"):
                for zona in zonas_disponibles: st.session_state[f"zona_{zona}"] = False
            st.markdown("---")
            for zona in zonas_disponibles:
                if f"zona_{zona}" not in st.session_state:
                    st.session_state[f"zona_{zona}"] = True
                st.checkbox(zona, key=f"zona_{zona}")
        
        zonas_seleccionadas = [z for z in zonas_disponibles if st.session_state.get(f"zona_{z}", True)]
        st.caption(f"{len(zonas_seleccionadas)} de {len(zonas_disponibles)} zonas seleccionadas.")
        st.markdown("---")

        # 2. Filtramos el dataframe base
        df_tabla_base = df_resultados_zona[df_resultados_zona['Zona'].isin(zonas_seleccionadas)]

        if df_tabla_base.empty:
            st.warning("Selecciona al menos una zona para ver los resultados.")
        else:
            datos_agregados_charts = df_tabla_base.groupby('Franja_Meta').agg(
                Meta_Total=('Meta_Total', 'sum'),
                Recaudo_Total=('Recaudo_Total', 'sum'),
                Recaudo_Sin_Anti_Total=('Recaudo_Sin_Anti_Total', 'sum'),
                Recaudo_Meta_Total=('Recaudo_Meta_Total', 'sum')
            ).reset_index()
            datos_agregados_charts['Cumplimiento_%'] = (datos_agregados_charts['Recaudo_Total'] / datos_agregados_charts['Meta_Total']).fillna(0)
            
            col_izquierda, col_derecha = st.columns([2, 1])

            # --- Columna Izquierda: Cuadrícula de 2x2 para las franjas ---
            with col_izquierda:
                franjas_a_mostrar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
                
                fila1_cols = st.columns(2)
                fila2_cols = st.columns(2)
                
                grid_cols = fila1_cols + fila2_cols

                for col, franja in zip(grid_cols, franjas_a_mostrar):
                    with col:
                        data_row = datos_agregados_charts[datos_agregados_charts['Franja_Meta'] == franja]
                        if not data_row.empty:
                            fig_gauge = charts_resultados.create_gauge_chart( # Usamos tu función
                                value=data_row['Cumplimiento_%'].iloc[0],
                                meta=data_row['Meta_Total'].iloc[0],
                                recaudo=data_row['Recaudo_Total'].iloc[0],
                                faltante=data_row['Meta_Total'].iloc[0] - data_row['Recaudo_Total'].iloc[0],
                                title=f"{franja}" # Título específico para cada gráfico
                            )
                            st.plotly_chart(fig_gauge, use_container_width=True)
                        else:
                            st.warning(f"Sin datos para franja {franja}.")
            
            # --- Columna Derecha: Gráfico grande para el total ---
            with col_derecha:
                st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
                total_recaudo_sin_anti = datos_agregados_charts['Recaudo_Sin_Anti_Total'].sum()
                total_recaudo_meta = datos_agregados_charts['Recaudo_Meta_Total'].sum()
                cumplimiento_sin_anti = (total_recaudo_sin_anti / total_recaudo_meta) if total_recaudo_meta > 0 else 0
                
                titulo_grafico_total = f"T.R ({len(zonas_seleccionadas)} Zonas)"

                fig_gauge_total = charts_resultados.create_gauge_chart( # Usamos tu función
                    value=cumplimiento_sin_anti,
                    meta=total_recaudo_meta,
                    recaudo=total_recaudo_sin_anti,
                    faltante=total_recaudo_meta - total_recaudo_sin_anti,
                    title=titulo_grafico_total
                )
                st.plotly_chart(fig_gauge_total, use_container_width=True)
            st.markdown("---")
            
            # --- Sección de Tablas de Detalle por Zona ---
            st.header("Tabla de Detalle por Zona")

            expected_compliance, start_date, end_date = charts_resultados.calculate_expected_compliance()
            st.info(f"**Meta de cumplimiento para hoy ({date.today().strftime('%d/%m/%Y')}): {expected_compliance:.2%}** | "
                      f"Periodo: {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}")
            st.markdown("---")

            for franja in franjas_a_mostrar:
                st.subheader(f"Detalle para Franja: {franja}")
                df_tabla_franja = df_tabla_base[df_tabla_base['Franja_Meta'] == franja].copy()

                if df_tabla_franja.empty:
                    st.write("Sin datos para esta franja.")
                    st.markdown("---")
                    continue
                
                # Preparación de la tabla para visualización (sin cambios)
                df_tabla_franja['Faltante ($)'] = df_tabla_franja['Meta_Total'] - df_tabla_franja['Recaudo_Total']
                df_tabla_display = df_tabla_franja.rename(columns={
                    'Franja_Meta': 'Franja', 'Meta_Total': 'Meta ($)', 'Recaudo_Total': 'Recaudo ($)',
                    'Cumplimiento_%': 'Cumplimiento (%)', 'Regional_Cobro': 'Regional Cobro'
                })
                
                column_order = ['Regional Cobro', 'Zona', 'Franja', 'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)']
                df_tabla_display = df_tabla_display[[col for col in column_order if col in df_tabla_display.columns]]

                # 1. Volvemos a generar el objeto de estilo y lo convertimos a HTML
                styled_df = df_tabla_display.style.map(
                    lambda x: charts_resultados.style_cumplimiento_bar(x, expected_compliance),
                    subset=['Cumplimiento (%)']
                ).format({
                    'Meta ($)': '${:,.0f}', 'Recaudo ($)': '${:,.0f}',
                    'Faltante ($)': '${:,.0f}', 'Cumplimiento (%)': '{:.2%}'
                }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
                    {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
                ])
                
                html_table = styled_df.to_html()

                # 2. Usamos st.markdown para renderizar el HTML con los estilos
                if len(df_tabla_display) > 7:
                    st.markdown(
                        f'<div style="width: 100%; max-height: 350px; overflow-y: auto;">{html_table}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(html_table, unsafe_allow_html=True)
                
                df_for_excel = df_tabla_display.copy()
            
                # 2. Aplicamos el formato deseado a la columna 'Cumplimiento (%)'.
                df_for_excel['Cumplimiento (%)'] = df_for_excel['Cumplimiento (%)'].apply(
                    lambda x: f"{x * 100:.2f}".replace('.', ',') + '%'
                )

                # 3. Pasamos el nuevo DataFrame formateado a la función de descarga.
                charts_resultados.generate_excel_download_link( # Asumiendo que está disponible
                    df=df_for_excel,
                    filename=f"detalle_zonas_{franja.replace(' ', '_')}.xlsx",
                    button_label=f"📥 Descargar Datos de Franja {franja}"
                )
                st.markdown("---")

            # --- Sección de Métricas Totales (Zona) ---
            st.subheader("Totales Generales de Zonas Seleccionadas")
            total_meta = df_tabla_base['Meta_Total'].sum()
            total_recaudo = df_tabla_base['Recaudo_Total'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Meta Total", f"${total_meta:,.0f}")
            col2.metric("Recaudo Total", f"${total_recaudo:,.0f}")
            col3.metric("Faltante Total", f"${total_meta - total_recaudo:,.0f}")
            col4.metric("Cumplimiento Total", f"{(total_recaudo / total_meta) if total_meta > 0 else 0:.2%}")
    
    # --- NUEVA SECCIÓN: DETALLE POR COBRADOR ---
    st.markdown("---")
    st.header("Resultados de Cumplimiento por Cobrador")

    if df_resultados_cobrador is not None and not df_resultados_cobrador.empty:
        df_cobrador_display = df_resultados_cobrador.rename(columns={
            'Franja_Meta': 'Franja', 'Meta_Total': 'Meta ($)', 'Recaudo_Total': 'Recaudo ($)',
            'Cumplimiento_%': 'Cumplimiento (%)', 'Regional_Cobro': 'Regional Cobro'
        })
        
        # MODIFICACIÓN CLAVE: Incluir 'Faltante ($)' en el orden de columnas
        df_cobrador_display['Faltante ($)'] = df_cobrador_display['Meta ($)'] - df_cobrador_display['Recaudo ($)']
        column_order_cobrador = ['Regional Cobro', 'Cobrador', 'Franja', 'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)']
        
        df_cobrador_display = df_cobrador_display[[col for col in column_order_cobrador if col in df_cobrador_display.columns]]

        # 1. Volvemos a generar el objeto de estilo y lo convertimos a HTML
        expected_compliance, _, _ = charts_resultados.calculate_expected_compliance()
        styled_df_cobrador = df_cobrador_display.style.map(
            lambda x: charts_resultados.style_cumplimiento_bar(x, expected_compliance),
            subset=['Cumplimiento (%)']
        ).format({
            'Meta ($)': '${:,.0f}', 'Recaudo ($)': '${:,.0f}',
            'Faltante ($)': '${:,.0f}', 'Cumplimiento (%)': '{:.2%}'
        }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
            {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
        ])
        
        html_table_cobrador = styled_df_cobrador.to_html()

        st.info("Tabla con el detalle de recaudo y meta por cada Cobrador y Franja de Mora.")

        # Usamos st.markdown para renderizar el HTML con scroll si es necesario
        if len(df_cobrador_display) > 10:
            st.markdown(
                f'<div style="width: 100%; max-height: 450px; overflow-y: auto;">{html_table_cobrador}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(html_table_cobrador, unsafe_allow_html=True)
            
        # Preparar para descarga
        df_for_excel_cobrador = df_cobrador_display.copy()
        df_for_excel_cobrador['Cumplimiento (%)'] = df_for_excel_cobrador['Cumplimiento (%)'].apply(
            lambda x: f"{x * 100:.2f}".replace('.', ',') + '%'
        )

        charts_resultados.generate_excel_download_link(
            df=df_for_excel_cobrador,
            filename="detalle_cumplimiento_cobradores.xlsx",
            button_label="📥 Descargar Detalle de Cobradores"
        )
        st.markdown("---")

    else:
        st.info("No se encontraron datos de cumplimiento por Cobrador con los filtros seleccionados.")