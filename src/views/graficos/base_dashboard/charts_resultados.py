# charts_resultados.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data(ttl=3600)  # Aumentar TTL
def prepare_resultados_data(df, selected_empresas, selected_regionales):
    """
    Agrupa los datos de la cartera por Zona y Franja_Meta para calcular los totales,
    aplicando los filtros de la barra lateral.
    """
    # 1. Aplicamos los filtros de la barra lateral (excepto Franja_Meta)
    df_fuente = df[
        df["Empresa"].isin(selected_empresas) &
        df["Regional_Cobro"].isin(selected_regionales)
    ].copy()

    # 2. Seleccionamos solo las franjas que nos interesan
    franjas_a_usar = ['1 A 30', '31 A 90', '91 A 180', '181 A 360']
    df_filtrado = df_fuente[df_fuente['Franja_Meta'].isin(franjas_a_usar)]

    if df_filtrado.empty:
        return pd.DataFrame()

    # 3. Agrupamos y sumamos
    resultados = df_filtrado.groupby(['Zona', 'Franja_Meta']).agg(
        Meta_Total=('Meta_$', 'sum'),
        Recaudo_Total=('Total_Recaudo', 'sum')
    ).reset_index()

    # 4. Calculamos el cumplimiento
    resultados['Cumplimiento_%'] = 0.0
    mascara_meta_valida = resultados['Meta_Total'] > 0
    resultados.loc[mascara_meta_valida, 'Cumplimiento_%'] = (
        resultados.loc[mascara_meta_valida, 'Recaudo_Total'] / resultados.loc[mascara_meta_valida, 'Meta_Total']
    )

    return resultados

@st.cache_data(ttl=3600)  # Cachear también la creación de gráficos
def create_gauge_chart(value, meta, recaudo, title):
    """
    Crea un gráfico de velocímetro (medidor) optimizado.
    """
    gauge_value = value * 100 if value is not None else 0

    # OPTIMIZACIÓN: Configuración más ligera
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gauge_value,
        title={'text': title, 'font': {'size': 18, 'color': '#EAEAEA'}},
        number={'suffix': "%", 'font': {'size': 28, 'color': '#EAEAEA'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2B2B2B", 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,  # Reducir border
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 20], 'color': '#dc3545'},
                {'range': [20, 40], 'color': '#ffc107'},
                {'range': [40, 60], 'color': '#fdff9b'},
                {'range': [60, 80], 'color': '#90ee90'},
                {'range': [80, 100], 'color': '#28a745'}
            ],
            'threshold': {'line': {'color': "red", 'width': 3}, 'thickness': 0.75, 'value': 99.9}
        }))

    # OPTIMIZACIÓN: Layout más simple
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#EAEAEA", 'family': "Arial"},
        margin=dict(l=20, r=20, t=40, b=10),  # Margenes reducidos
        height=300  # Altura fija para consistencia
    )

    fig.add_annotation(
        x=0.5, y=0.15,
        text=f"Meta: ${meta:,.0f}<br>Recaudo: ${recaudo:,.0f}",
        showarrow=False,
        font=dict(size=12, color="#EAEAEA")  # Tamaño reducido
    )

    return fig