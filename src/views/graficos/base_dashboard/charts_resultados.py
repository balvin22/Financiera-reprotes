# charts_resultados.py
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import io


@st.cache_data(ttl=3600)  # Aumentar TTL

def prepare_resultados_data(df_filtrado_global):
    """
    Toma los datos de cartera YA FILTRADOS GLOBALMENTE y los agrupa
    por Zona y Franja_Meta, incluyendo los nuevos campos para el quinto gráfico.
    """
    franjas_a_usar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
    df_para_grupo = df_filtrado_global[df_filtrado_global['Franja_Meta'].isin(franjas_a_usar)]

    if df_para_grupo.empty:
        return pd.DataFrame()

    # Asegurarnos de que las columnas existan, si no, las creamos con 0
    if 'Total_Recaudo_Sin_Anti' not in df_para_grupo.columns:
        df_para_grupo['Total_Recaudo_Sin_Anti'] = 0
    if 'Meta_T.R_$' not in df_para_grupo.columns:
        df_para_grupo['Meta_T.R_$'] = 0

    group_by_cols = ['Zona', 'Franja_Meta']
    if 'Regional_Cobro' in df_para_grupo.columns:
        group_by_cols.insert(0, 'Regional_Cobro')

    resultados = df_para_grupo.groupby(group_by_cols).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Total_Recaudo', 'sum'),
        # NUEVO: Agregamos los campos para el quinto velocímetro
        Recaudo_Sin_Anti_Total=('Total_Recaudo_Sin_Anti', 'sum'),
        Recaudo_Meta_Total=('Meta_T.R_$', 'sum')
    ).reset_index()

    resultados['Cumplimiento_%'] = 0.0
    mascara_meta_valida = resultados['Meta_Total'] > 0
    resultados.loc[mascara_meta_valida, 'Cumplimiento_%'] = (
        resultados.loc[mascara_meta_valida, 'Recaudo_Total'] / resultados.loc[mascara_meta_valida, 'Meta_Total']
    )
    return resultados

st.cache_data(ttl=3600)
def aggregate_selected_zones(df_resultados, selected_zonas):
    """
    Toma los resultados pre-calculados y los agrega para un grupo de zonas seleccionadas.
    """
    if not selected_zonas or df_resultados.empty:
        return pd.DataFrame()

    df_filtrado = df_resultados[df_resultados['Zona'].isin(selected_zonas)]

    if df_filtrado.empty:
        return pd.DataFrame()

    df_agregado = df_filtrado.groupby('Franja_Meta').agg(
        Meta_Total=('Meta_Total', 'sum'),
        Recaudo_Total=('Recaudo_Total', 'sum'),
        # NUEVO: Agregamos los campos para el quinto velocímetro
        Recaudo_Sin_Anti_Total=('Recaudo_Sin_Anti_Total', 'sum'),
        Recaudo_Meta_Total=('Recaudo_Meta_Total', 'sum')
    ).reset_index()

    df_agregado['Cumplimiento_%'] = 0.0
    mascara_meta_valida = df_agregado['Meta_Total'] > 0
    df_agregado.loc[mascara_meta_valida, 'Cumplimiento_%'] = (
        df_agregado.loc[mascara_meta_valida, 'Recaudo_Total'] / df_agregado.loc[mascara_meta_valida, 'Meta_Total']
    )
    return df_agregado



# --- VERSIÓN MEJORADA DE LA FUNCIÓN DEL GRÁFICO ---
@st.cache_data(ttl=3600)
def create_gauge_chart(value, meta, recaudo, faltante, title):
    """
    Crea un gráfico de medidor con texto detallado en una anotación inferior.
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
        number={'suffix': "%", 'font': {'size': 32, 'color': text_color}},
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

    # --- ESTA ES LA PARTE CLAVE ---
    # Si esta anotación existe, el texto NO puede superponerse con el porcentaje.
    fig.add_annotation(
        x=0.5, y=0.05,
        text=f"Meta: ${meta:,.0f}<br>Recaudo: ${recaudo:,.0f}<br>Faltante: ${faltante:,.0f}",
        showarrow=False,
        font=dict(size=12, color=text_color),
        align="center"
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=280,
        margin=dict(l=10, r=10, t=50, b=10)
    )

    return fig

def calculate_expected_compliance():
    """
    Calcula el porcentaje de cumplimiento esperado para el día actual
    basado en un periodo ESTANDARIZADO de 30.5 días.
    El ciclo sigue siendo del 5 de un mes al 4 del siguiente.
    """
    today = date.today()
    
    # 1. Se calcula el inicio y fin del periodo para saber cuántos días han pasado
    if today.day >= 5:
        start_date = today.replace(day=5)
        end_date = (today + relativedelta(months=1)).replace(day=4)
    else:
        start_date = (today - relativedelta(months=1)).replace(day=5)
        end_date = today.replace(day=4)

    elapsed_days = min((today - start_date).days + 1, 30.5) # No puede pasar de 30.5
    total_days_in_period = 30.5
    
    # 3. Se calcula el cumplimiento esperado con la base fija
    if elapsed_days > 0:
        expected_compliance = elapsed_days / total_days_in_period
    else:
        expected_compliance = 0.0
        
    return expected_compliance, start_date, end_date

# --- FUNCIÓN MODIFICADA: Ahora recibe el valor esperado ---
def style_cumplimiento_bar(cumplimiento_real, expected_compliance):
    """
    Aplica un estilo de barra de progreso comparando el valor real
    con el esperado, y normaliza visualmente los valores > 100%.
    """
    # --- 1. Lógica de Color Mejorada ---
    diferencia = expected_compliance - cumplimiento_real
    
    # <-- NUEVA LÓGICA DE COLOR PARA SOBRECUMPLIMIENTO -->
    if cumplimiento_real >= 1:
        color = "#06301a" 
    elif cumplimiento_real >= expected_compliance:
        color = '#28a745'  # Verde
    elif diferencia <= 0.20:  # Amarillo
        color = '#ffc107'
    else:  # Rojo
        color = '#dc3545'

    # --- 2. Normalización del Valor para la Barra Visual ---
    valor_barra_numerico = cumplimiento_real * 100
    
    # <-- CAMBIO CLAVE: El valor para el gradiente se limita a un máximo de 100 -->
    valor_barra_visual = min(valor_barra_numerico, 100)
    
    # --- 3. Creación de Estilos ---
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
    """
    Genera un botón de Streamlit para descargar un DataFrame como un archivo Excel.
    """
    output = io.BytesIO()
    # Usamos el motor 'openpyxl' que es el estándar moderno
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    
    excel_data = output.getvalue()

    st.download_button(
        label=button_label,
        data=excel_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
