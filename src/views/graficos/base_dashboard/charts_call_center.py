import streamlit as st
import pandas as pd
import charts_resultados
import plotly.express as px
from datetime import date



def render(tab6_data):
    """
    Renderiza el contenido del Tab 6: Call Centers, aplicando la lógica de meta de cumplimiento
    y el estilo condicional a la tabla.
    """
    st.header("Análisis de Rendimiento de Call Centers")

    if not tab6_data or not any(key in tab6_data for key in ["reporte_raw", "rodamiento_data"]):
        st.warning("No hay datos de Call Center para mostrar con los filtros seleccionados.")
        return

    # Extraemos los dataframes del diccionario
    df_raw = tab6_data.get("reporte_raw", pd.DataFrame())
    df_display = tab6_data.get("reporte_display", pd.DataFrame())
    df_rodamiento = tab6_data.get("rodamiento_data", pd.DataFrame())

    # --- 1. Calcular y mostrar la Meta de Cumplimiento Diaria ---
    expected_compliance, start_date, end_date = charts_resultados.calculate_expected_compliance()
    st.info(f"**Meta de cumplimiento para hoy ({date.today().strftime('%d/%m/%Y')}): {expected_compliance:.2%}** | "
            f"Periodo: {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        # ... (Código del gráfico de cumplimiento sin cambios) ...
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

    with col2:
        # ... (Código del gráfico de Rodamientos sin cambios) ...
        if not df_rodamiento.empty:
            st.subheader("Rodamientos en Call Centers")
            fig_pie = px.pie(
                df_rodamiento,
                names='Rodamiento',
                values='count',
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent')
            fig_pie.update_layout(showlegend=True, legend_title_text='Rodamiento', margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos para el gráfico de rodamientos.")

    st.markdown("---")

    # --- 2. Tabla de Detalle de Call Centers con Estilo Condicional ---
    if not df_raw.empty:
        st.subheader("Tabla de Detalle de Call Centers")
        
        # Preparamos el DataFrame de visualización
        df_styled = df_raw.copy()
        df_styled = df_styled.rename(columns={
            'META_$': 'Meta ($)', 
            'Recaudo_Meta': 'Recaudo ($)',
            'Cumplimiento': 'Cumplimiento (%)', # Usamos el valor float para el mapeo
            'NOMBRE': 'Nombre',
            'Faltante': 'Faltante ($)'
        })
        
        column_order = ['CALL_CENTER', 'Nombre', 'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)']
        df_styled = df_styled[column_order]

        # Aplicar el estilo condicional y formato
        styled_df = df_styled.style.map(
            lambda x: charts_resultados.style_cumplimiento_bar(x, expected_compliance),
            subset=['Cumplimiento (%)']
        ).format({
            # Formateo de moneda con separador de miles y decimal
            'Meta ($)': '${:,.0f}', 'Recaudo ($)': '${:,.0f}',
            'Faltante ($)': '${:,.0f}', 
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