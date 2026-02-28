import streamlit as st
import charts_resultados 
from datetime import date

def render(tab3_data): 
    """
    Renderiza el contenido de la pestaña "Resultados".
    """ 
    if tab3_data is None or not isinstance(tab3_data, dict):
        st.warning("No se encontraron datos de resultados para los filtros globales seleccionados.")
        return

    df_resultados_zona = tab3_data.get("resultados_zona", None)
    df_resultados_cobrador = tab3_data.get("resultados_cobrador", None)

    if df_resultados_zona is None or df_resultados_zona.empty:
        st.warning("No se encontraron datos de resultados de ZONA para los filtros globales seleccionados.")
        return # Cortamos aquí para evitar errores de gráficos vacíos
    
    # --- GRÁFICOS DE ZONAS ---
    st.header("Resultados de Cumplimiento por Zona y Franja")
    st.markdown("---")

    # Usamos directamente el DataFrame que ya viene filtrado desde el Sidebar
    df_tabla_base = df_resultados_zona.copy()
    zonas_unicas = df_tabla_base['Zona'].nunique() if 'Zona' in df_tabla_base.columns else 0

    datos_agregados_charts = df_tabla_base.groupby('Franja_Meta').agg(
        Meta_Total=('Meta_Total', 'sum'),
        Recaudo_Total=('Recaudo_Total', 'sum'),
        Recaudo_Sin_Anti_Total=('Recaudo_Sin_Anti_Total', 'sum'),
        Recaudo_Meta_Total=('Recaudo_Meta_Total', 'sum')
    ).reset_index()
    
    datos_agregados_charts['Cumplimiento_%'] = (datos_agregados_charts['Recaudo_Total'] / datos_agregados_charts['Meta_Total']).fillna(0)
    
    col_izquierda, col_derecha = st.columns([2, 1])

    # --- Columna Izquierda: Gráficos ---
    with col_izquierda:
        franjas_a_mostrar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
        
        fila1_cols = st.columns(2)
        fila2_cols = st.columns(2)
        grid_cols = fila1_cols + fila2_cols

        for col, franja in zip(grid_cols, franjas_a_mostrar):
            with col:
                data_row = datos_agregados_charts[datos_agregados_charts['Franja_Meta'] == franja]
                if not data_row.empty:
                    fig_gauge = charts_resultados.create_gauge_chart(
                        value=data_row['Cumplimiento_%'].iloc[0],
                        meta=data_row['Meta_Total'].iloc[0],
                        recaudo=data_row['Recaudo_Total'].iloc[0],
                        faltante=data_row['Meta_Total'].iloc[0] - data_row['Recaudo_Total'].iloc[0],
                        title=f"{franja}"
                    )
                    st.plotly_chart(fig_gauge, use_container_width=True)
                else:
                    st.warning(f"Sin datos para franja {franja}.")
        
    # --- Columna Derecha: Gráfico Total ---
    with col_derecha:
        st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
        total_recaudo_sin_anti = datos_agregados_charts['Recaudo_Sin_Anti_Total'].sum()
        total_recaudo_meta = datos_agregados_charts['Recaudo_Meta_Total'].sum()
        cumplimiento_sin_anti = (total_recaudo_sin_anti / total_recaudo_meta) if total_recaudo_meta > 0 else 0
        
        # El título ahora se adapta automáticamente a las zonas que vengan del filtro general
        titulo_grafico_total = f"T.R ({zonas_unicas} Zonas)"

        fig_gauge_total = charts_resultados.create_gauge_chart(
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
        df_tabla_franja = df_tabla_base[df_tabla_base['Franja_Meta'] == franja].copy()

        if df_tabla_franja.empty:
            st.subheader(f"Detalle para Franja: {franja}")
            st.write("Sin datos para esta franja.")
            st.markdown("---")
            continue
        
        total_cuentas_franja = df_tabla_franja['Cant_Cuentas'].sum()

        st.subheader(f"Detalle para Franja: {franja}")
        st.markdown(f"#### 👥 Total Cuentas Asociadas: :blue[{total_cuentas_franja:,.0f}]")
        
        df_tabla_franja['Faltante ($)'] = df_tabla_franja['Meta_Total'] - df_tabla_franja['Recaudo_Total']
        
        df_tabla_display = df_tabla_franja.rename(columns={
            'Franja_Meta': 'Franja', 
            'Meta_Total': 'Meta ($)', 
            'Recaudo_Total': 'Recaudo ($)',
            'Cumplimiento_%': 'Cumplimiento (%)', 
            'Regional_Cobro': 'Regional Cobro',
            'Cant_Cuentas': '# Cuentas' 
        })
        
        column_order = [
            'Regional Cobro', 'Zona', 'Franja', '# Cuentas', 
            'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)'
        ]
        df_tabla_display = df_tabla_display[[col for col in column_order if col in df_tabla_display.columns]]

        styled_df = df_tabla_display.style.map(
            lambda x: charts_resultados.style_cumplimiento_bar(x, expected_compliance),
            subset=['Cumplimiento (%)']
        ).format({
            '# Cuentas': '{:,.0f}', 
            'Meta ($)': '${:,.0f}', 
            'Recaudo ($)': '${:,.0f}',
            'Faltante ($)': '${:,.0f}', 
            'Cumplimiento (%)': '{:.2%}'
        }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
            {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
        ])
        
        html_table = styled_df.to_html()

        if len(df_tabla_display) > 7:
            st.markdown(
                f'<div style="width: 100%; max-height: 350px; overflow-y: auto;">{html_table}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(html_table, unsafe_allow_html=True)
        
        df_for_excel = df_tabla_display.copy()
        df_for_excel['Cumplimiento (%)'] = df_for_excel['Cumplimiento (%)'].apply(
            lambda x: f"{x * 100:.2f}".replace('.', ',') + '%'
        )

        charts_resultados.generate_excel_download_link(
            df=df_for_excel,
            filename=f"detalle_zonas_{franja.replace(' ', '_')}.xlsx",
            button_label=f"📥 Descargar Datos de Franja {franja}"
        )
        st.markdown("---")

    # --- Sección de Métricas Totales (Zona) ---
    st.subheader("Totales Generales de Zonas Seleccionadas")
    total_meta = df_tabla_base['Meta_Total'].sum()
    total_recaudo = df_tabla_base['Recaudo_Total'].sum()
    total_cuentas_global = df_tabla_base['Cant_Cuentas'].sum()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Meta Total", f"${total_meta:,.0f}")
    col2.metric("Recaudo Total", f"${total_recaudo:,.0f}")
    col3.metric("Faltante Total", f"${total_meta - total_recaudo:,.0f}")
    col4.metric("Cumplimiento", f"{(total_recaudo / total_meta) if total_meta > 0 else 0:.2%}")
    col5.metric("Total Cuentas", f"{total_cuentas_global:,.0f}")
    
    # --- DETALLE POR COBRADOR ---
    st.markdown("---")
    st.header("Detalle para franja: TR")

    if df_resultados_cobrador is not None and not df_resultados_cobrador.empty:
        
        df_cobrador_display = df_resultados_cobrador.rename(columns={
            'Meta_Total': 'Meta T.R ($)',      
            'Recaudo_Total': 'Recaudo ($)',
            'Cumplimiento_%': 'Cumplimiento (%)', 
            'Regional_Cobro': 'Regional Cobro',
            'Cant_Cuentas': '# Cuentas'
        })
        
        df_cobrador_display['Faltante ($)'] = df_cobrador_display['Meta T.R ($)'] - df_cobrador_display['Recaudo ($)']
        
        column_order_cobrador = [
            'Regional Cobro', 'Zona', 'Cobrador', '# Cuentas', 
            'Meta T.R ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)'
        ]
        
        df_cobrador_display = df_cobrador_display[[col for col in column_order_cobrador if col in df_cobrador_display.columns]]

        if 'Zona' in df_cobrador_display.columns:
             df_cobrador_display = df_cobrador_display.sort_values(by=['Zona', 'Cumplimiento (%)'], ascending=[True, False])
        else:
             df_cobrador_display = df_cobrador_display.sort_values(by='Cumplimiento (%)', ascending=False)

        expected_compliance, _, _ = charts_resultados.calculate_expected_compliance()
        styled_df_cobrador = df_cobrador_display.style.map(
            lambda x: charts_resultados.style_cumplimiento_bar(x, expected_compliance),
            subset=['Cumplimiento (%)']
        ).format({
            '# Cuentas': '{:,.0f}',
            'Meta T.R ($)': '${:,.0f}',  
            'Recaudo ($)': '${:,.0f}',
            'Faltante ($)': '${:,.0f}', 
            'Cumplimiento (%)': '{:.2%}'
        }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
            {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
        ])
        
        html_table_cobrador = styled_df_cobrador.to_html()

        st.info("Tabla con el detalle de recaudo y Meta T.R por cada Cobrador (Acumulado).")

        if len(df_cobrador_display) > 10:
            st.markdown(
                f'<div style="width: 100%; max-height: 450px; overflow-y: auto;">{html_table_cobrador}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(html_table_cobrador, unsafe_allow_html=True)
            
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