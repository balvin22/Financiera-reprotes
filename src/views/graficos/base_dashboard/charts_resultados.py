import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import io

def create_gauge_chart(value, meta, recaudo, faltante, title):
    """
    Crea un gráfico de medidor con texto detallado en una anotación inferior.
    Esta función solo se encarga de la visualización.
    """
    try:
        theme_base = st.get_option("theme.base")
        text_color = '#EAEAEA' if theme_base == "dark" else '#333333'
    except Exception:
        text_color = '#EAEAEA'
        
    gauge_value = value * 100 if value is not None else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gauge_value,
        title={'text': title, 'font': {'size': 20, 'color': text_color}},
        number={'suffix': "%", 'font': {'size': 30, 'color': text_color}}, # Font size reduced slightly
        
        # --- CAMBIO 1: Subimos el medidor para crear espacio abajo ---
        domain={'y': [0.23, 1]},
        
        gauge={
            'axis': {'range': [0, 130]},
            'bar': {'color': "rgba(0,0,0,0.3)", 'thickness': 0.15},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#d9534f'},
                {'range': [40, 60], 'color': '#f0ad4e'},
                {'range': [60, 80], 'color': '#e6f5c9'},
                {'range': [80, 100], 'color': '#5cb85c'},
                {'range': [100, 130], 'color': '#663399'}
            ],
            'threshold': {'line': {'color': text_color, 'width': 3}, 'thickness': 0.9, 'value': 100}
        }))
        
    # --- CAMBIO 2: Bajamos la anotación al nuevo espacio creado ---
    fig.add_annotation(
        x=0.5, y=0.05, # La posición 'y' ahora funciona gracias al 'domain' de arriba
        text=f"Meta: ${meta:,.0f}<br>Recaudo: ${recaudo:,.0f}<br>Faltante: ${faltante:,.0f}",
        showarrow=False,
        font=dict(size=11, color=text_color),
        align="center"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=280,
        # --- CAMBIO 3: Aumentamos el margen inferior para que el texto no se corte ---
        margin=dict(l=10, r=10, t=50, b=10) 
    )
    return fig

def calculate_expected_compliance():
    today = date.today()
    if today.day >= 5:
        start_date = today.replace(day=5)
        end_date = (today + relativedelta(months=1)).replace(day=4)
    else:
        start_date = (today - relativedelta(months=1)).replace(day=5)
        end_date = today.replace(day=4)
    elapsed_days = min((today - start_date).days + 1, 30.5)
    total_days_in_period = 30.5
    if elapsed_days > 0:
        expected_compliance = elapsed_days / total_days_in_period
    else:
        expected_compliance = 0.0
    return expected_compliance, start_date, end_date

def style_cumplimiento_bar(cumplimiento_real, expected_compliance):
    diferencia = expected_compliance - cumplimiento_real
    if cumplimiento_real >= 1:
        color = "#06301a" 
    elif cumplimiento_real >= expected_compliance:
        color = '#28a745'
    elif diferencia <= 0.20:
        color = '#ffc107'
    else:
        color = '#dc3545'
    valor_barra_numerico = cumplimiento_real * 100
    valor_barra_visual = min(valor_barra_numerico, 100)
    styles = {
        'background': f"linear-gradient(90deg, {color} {valor_barra_visual}%, #33333330 {valor_barra_visual}%)",
        'color': 'white',
        'text-shadow': '1px 1px 2px black',
        'font-weight': 'bold',
        'text-align': 'center',
        'padding': '5px 0'
    }
    return '; '.join([f'{key}: {value}' for key, value in styles.items()])

def generate_excel_download_link(df, filename, button_label):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    excel_data = output.getvalue()
    st.download_button(
        label=button_label,
        data=excel_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )