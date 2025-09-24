# charts_metricas.py
import plotly.express as px

def create_regional_bar_chart(df_agg):
    """Crea un gráfico de barras por Regional de Venta."""
    # <-- YA NO HAY PROCESAMIENTO DE DATOS AQUÍ
    fig = px.bar(
        df_agg, x='Regional_Venta', y='count', color='Franja_Meta',
        title="<b>Total de Cuentas por Regional</b>",
        labels={'count': 'Cantidad de Cuentas', 'Regional_Venta': 'Regional', 'Franja_Meta': 'Franja'},
        template='plotly_white', text_auto=True
    )
    return fig

def create_cobro_bar_chart(df_agg):
    """Crea un gráfico de barras por Grupo de Cobro."""
    if df_agg is None or df_agg.empty:
        return None
    # <-- YA NO HAY PROCESAMIENTO DE DATOS AQUÍ
    fig = px.bar(
        df_agg, x='Eje_X_Cobro', y='count', color='Franja_Meta',
        title="<b>Total de Cuentas por Grupo de Cobro</b>",
        labels={'count': 'Cantidad de Cuentas', 'Eje_X_Cobro': 'Grupo de Cobro', 'Franja_Meta': 'Franja'},
        template='plotly_white', text_auto=True
    )
    return fig

def create_desembolso_por_ano_chart(df_agg):
    """Crea un gráfico de barras del valor desembolsado por año."""
    if df_agg is None or df_agg.empty:
        return None
    # <-- YA NO HAY PROCESAMIENTO DE DATOS AQUÍ
    fig = px.bar(
        df_agg,
        x='Año_Desembolso', y='Valor_Desembolso', color='Franja_Meta',
        title=f"<b>Valor Desembolsado</b>",
        labels={'Año_Desembolso': 'Año', 'Valor_Desembolso': 'Suma Valor ($)', 'Franja_Meta': 'Franja'},
        template='plotly_white', text_auto='.2s'
    )
    fig.update_layout(xaxis={'type': 'category'})
    fig.update_traces(textposition='inside')
    return fig

def create_vigencia_sunburst_chart(df_agg):
    """Crea un gráfico de sol (sunburst) mostrando la distribución de cuotas."""
    if df_agg is None or df_agg.empty:
        return None
    # <-- YA NO HAY PROCESAMIENTO DE DATOS AQUÍ
    fig = px.sunburst(
        df_agg,
        path=['Estado_Vigencia_Agrupado', 'Sub_Estado_Vigencia'],
        values='count',
        title="<b>Distribución de Cuotas por Estado de Vigencia</b>",
        color='Estado_Vigencia_Agrupado',
        template='plotly_white'
    )
    fig.update_traces(
        textinfo='label+percent parent', insidetextorientation='radial', sort=True
    )
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))
    return fig