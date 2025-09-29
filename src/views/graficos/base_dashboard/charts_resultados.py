# charts_resultados.py
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

@st.cache_data(ttl=3600)  # Aumentar TTL
def prepare_resultados_data(df_filtrado_global):
    """
    Toma los datos de cartera YA FILTRADOS GLOBALMENTE y los agrupa
    por Zona y Franja_Meta para calcular los totales.
    """
    # 1. Ya no necesitamos filtrar por empresa o regional aquí.
    # Los datos ya vienen listos.
    
    # 2. Seleccionamos solo las franjas que nos interesan
    franjas_a_usar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
    df_para_grupo = df_filtrado_global[df_filtrado_global['Franja_Meta'].isin(franjas_a_usar)]

    if df_para_grupo.empty:
        return pd.DataFrame()

    # 3. Agrupamos y sumamos
    resultados = df_para_grupo.groupby(['Zona', 'Franja_Meta']).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Total_Recaudo', 'sum')
    ).reset_index()

    # 4. Calculamos el cumplimiento (sin cambios)
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

    # 1. Filtramos para quedarnos solo con las zonas que el usuario eligió
    df_filtrado = df_resultados[df_resultados['Zona'].isin(selected_zonas)]

    if df_filtrado.empty:
        return pd.DataFrame()

    # 2. Agrupamos por Franja y sumamos los totales de las zonas seleccionadas
    df_agregado = df_filtrado.groupby('Franja_Meta').agg(
        Meta_Total=('Meta_Total', 'sum'),
        Recaudo_Total=('Recaudo_Total', 'sum')
    ).reset_index()

    # 3. Recalculamos el cumplimiento con los nuevos totales agregados
    df_agregado['Cumplimiento_%'] = 0.0
    mascara_meta_valida = df_agregado['Meta_Total'] > 0
    df_agregado.loc[mascara_meta_valida, 'Cumplimiento_%'] = (
        df_agregado.loc[mascara_meta_valida, 'Recaudo_Total'] / df_agregado.loc[mascara_meta_valida, 'Meta_Total']
    )

    return df_agregado


# --- VERSIÓN MEJORADA DE LA FUNCIÓN DEL GRÁFICO ---
@st.cache_data(ttl=3600)
def create_gauge_chart(value, meta, recaudo, title):
    """
    Crea un gráfico de velocímetro (medidor) que se adapta
    automáticamente al tema claro u oscuro de Streamlit y muestra hasta un 130%.
    """
    # ... (la detección del tema y la definición de colores se mantienen igual) ...
    theme_base = st.get_option("theme.base")
    if theme_base == "dark":
        text_color, bar_color, border_color = '#EAEAEA', '#2B2B2B', 'gray'
    else:
        text_color, bar_color, border_color = '#333333', '#EEEEEE', 'darkgray'

    gauge_value = value * 100 if value is not None else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gauge_value,
        title={'text': title, 'font': {'size': 18, 'color': text_color}},
        number={'suffix': "%", 'font': {'size': 28, 'color': text_color}},
        gauge={
            # <-- CAMBIO 1: Ampliamos el rango del eje hasta 130
            'axis': {'range': [None, 130], 'tickwidth': 1, 'tickcolor': text_color},
            'bar': {'color': bar_color, 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': border_color,
            'steps': [
                {'range': [0, 20], 'color': '#dc3545'},
                {'range': [20, 40], 'color': '#ffc107'},
                {'range': [40, 60], 'color': '#fdff9b'},
                {'range': [60, 80], 'color': '#90ee90'},
                {'range': [80, 100], 'color': '#28a745'},
                # <-- CAMBIO 2: Añadimos un nuevo escalón de color para el sobrecumplimiento
                {'range': [100, 130], 'color': '#6f42c1'} # Un color morado para indicar "extra"
            ],
            # <-- CAMBIO 3: Ponemos una línea gruesa justo en el 100% para marcar la meta
            'threshold': {'line': {'color': text_color, 'width': 4}, 'thickness': 1.0, 'value': 100}
        }))

    # ... (el resto de la función, incluyendo update_layout y add_annotation, se mantiene igual) ...
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': text_color, 'family': "Arial"},
        margin=dict(l=20, r=20, t=40, b=10),
        height=300
    )
    fig.add_annotation(
        x=0.5, y=0.15,
        text=f"Meta: ${meta:,.0f}<br>Recaudo: ${recaudo:,.0f}",
        showarrow=False,
        font=dict(size=12, color=text_color)
    )

    return fig

def calculate_expected_compliance():
    """
    Calcula el porcentaje de cumplimiento esperado para el día actual
    basado en el ciclo de cobro (5 de un mes al 4 del siguiente).
    Retorna el valor esperado (ej: 0.83) y las fechas del periodo.
    """
    today = date.today()
    
    # Define el inicio y fin del periodo de cobro actual
    if today.day >= 5:
        start_date = today.replace(day=5)
        end_date = (today + relativedelta(months=1)).replace(day=4)
    else:
        start_date = (today - relativedelta(months=1)).replace(day=5)
        end_date = today.replace(day=4)

    total_days_in_period = (end_date - start_date).days + 1
    # Asegurarse de que los días transcurridos no superen el total del período
    elapsed_days = min((today - start_date).days + 1, total_days_in_period)
    
    if total_days_in_period > 0 and elapsed_days > 0:
        expected_compliance = elapsed_days / total_days_in_period
    else:
        expected_compliance = 0.0
        
    return expected_compliance, start_date, end_date

# --- FUNCIÓN MODIFICADA: Ahora recibe el valor esperado ---
def style_cumplimiento_bar(cumplimiento_real, expected_compliance):
    """
    Aplica un estilo de barra de progreso comparando el valor real
    con el esperado (que se pasa como argumento).
    """
    # La lógica de cálculo de fecha se movió a la función anterior.
    # Ahora solo determina el color y crea el estilo.

    diferencia = expected_compliance - cumplimiento_real
    
    if cumplimiento_real >= expected_compliance:
        color = '#28a745'  # Verde: Cumplido o superado
    elif diferencia <= 0.20:  # Amarillo: Cerca (hasta 20% por debajo)
        color = '#ffc107'
    else:  # Rojo: Lejos
        color = '#dc3545'

    valor_barra = cumplimiento_real * 100
    
    style = (
        f"background: linear-gradient(90deg, {color} {valor_barra}%, #55555530 {valor_barra}%); "
        "color: white; "
        "text-shadow: 1px 1px 2px black; "
        "font-weight: bold;"
    )
    
    return style
