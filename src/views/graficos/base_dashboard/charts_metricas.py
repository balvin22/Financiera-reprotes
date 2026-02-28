# charts_metricas.py
import plotly.express as px

# --- 1. Definimos una paleta de colores constante ---
COLOR_MAP_FRANJAS = {
    'AL DIA': '#2ECC71',       # Verde
    '1 A 30': '#F1C40F',       # Amarillo
    '31 A 90': '#E67E22',      # Naranja
    '91 A 180': '#E74C3C',     # Rojo claro
    '181 A 360': '#C0392B',    # Rojo oscuro
    '> 360': '#7B241C',        # Vino
    'MAS DE 360': '#7B241C',   # Vino
    'nan': '#BDC3C7'           # Gris
}

# Orden fijo para que el verde siempre quede abajo y el rojo arriba
ORDEN_LOGICO = ['AL DIA', '1 A 30', '31 A 90', '91 A 180', '181 A 360', '> 360', 'MAS DE 360']

def _add_totals_to_bars(fig, df_agg, x_col, y_col):
    """Añade el total encima de cada barra apilada de forma segura."""
    # Agrupamos sumando los totales por cada barra (ej. todo Bordo, todo Pasto)
    totals = df_agg.groupby(x_col, observed=False)[y_col].sum().reset_index()
    for _, row in totals.iterrows():
        val = row[y_col]
        # Formateamos con separador de miles
        texto = f"{val:,.0f}".replace(',', '.')
            
        fig.add_annotation(
            x=row[x_col],
            y=val,
            text=f"<b>{texto}</b>",
            showarrow=False,
            yshift=12, # Sube el número un poquito para que no toque la barra
            font=dict(size=12, color="#333333")
        )
    return fig

def create_regional_bar_chart(df_agg):
    if df_agg is None or df_agg.empty:
        return None
        
    fig = px.bar(
        df_agg, 
        x='Regional_Venta', 
        y='count', 
        color='Franja_Meta',
        title="<b>Total de Cuentas por Regional</b>",
        labels={'count': 'Cantidad', 'Regional_Venta': 'Regional', 'Franja_Meta': 'Franja'},
        template='plotly_white',
        color_discrete_map=COLOR_MAP_FRANJAS,
        category_orders={"Franja_Meta": ORDEN_LOGICO}
    )
    
    fig.update_traces(hovertemplate="%{y} cuentas")
    
    fig.update_layout(
        xaxis=dict(type='category'),
        bargap=0.3, 
        barmode='stack', 
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.95)", font_size=13)
    )
    
    # SÍ agregamos el total aquí
    fig = _add_totals_to_bars(fig, df_agg, 'Regional_Venta', 'count')
    return fig

def create_cobro_bar_chart(df_agg):
    if df_agg is None or df_agg.empty:
        return None
        
    fig = px.bar(
        df_agg, 
        x='Eje_X_Cobro', 
        y='count', 
        color='Franja_Meta',
        title="<b>Total de Cuentas por Grupo de Cobro</b>",
        labels={'count': 'Cantidad', 'Eje_X_Cobro': 'Grupo de Cobro', 'Franja_Meta': 'Franja'},
        template='plotly_white',
        color_discrete_map=COLOR_MAP_FRANJAS,
        category_orders={"Franja_Meta": ORDEN_LOGICO}
    )
    
    fig.update_traces(hovertemplate="%{y} cuentas")
    
    fig.update_layout(
        xaxis=dict(type='category'), 
        bargap=0.3, 
        barmode='stack', 
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.95)", font_size=13)
    )
    
    # SÍ agregamos el total aquí
    fig = _add_totals_to_bars(fig, df_agg, 'Eje_X_Cobro', 'count')
    return fig

def create_desembolso_por_ano_chart(df_agg):
    if df_agg is None or df_agg.empty:
        return None
        
    df_chart = df_agg.copy()
    df_chart['Año_Desembolso'] = df_chart['Año_Desembolso'].astype(str).str.strip()
        
    fig = px.bar(
        df_chart,
        x='Año_Desembolso', 
        y='Valor_Desembolso', 
        color='Franja_Meta',
        title=f"<b>Valor Desembolsado por Año</b>",
        labels={'Año_Desembolso': 'Año', 'Valor_Desembolso': 'Desembolsado ($)', 'Franja_Meta': 'Franja'},
        template='plotly_white',
        color_discrete_map=COLOR_MAP_FRANJAS,
        category_orders={"Franja_Meta": ORDEN_LOGICO}
    )
    
    # Formato moneda para el hover
    fig.update_traces(hovertemplate="$%{y:,.0f}")
    
    fig.update_layout(
        xaxis=dict(type='category'), 
        bargap=0.3, 
        barmode='stack', 
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.95)", font_size=13)
    )
    
    # NO agregamos el total manual aquí para proteger la estructura del eje de tiempo
    return fig

def create_vigencia_sunburst_chart(df_agg):
    if df_agg is None or df_agg.empty:
        return None

    color_map = {
        'VIGENTES': '#90ee90',
        'VIGENCIA EXPIRADA': '#FF6B6B',
        'ANTICIPADO': '#add8e6'
    }
    
    fig = px.sunburst(
        df_agg,
        path=['Estado_Vigencia_Agrupado', 'Sub_Estado_Vigencia'],
        values='count',
        title="<b>Distribución de Cuotas por Estado</b>",
        color='Estado_Vigencia_Agrupado',
        template='plotly_white',
        color_discrete_map=color_map
    )
    
    fig.update_traces(
        textinfo='label+percent parent', 
        insidetextorientation='radial', 
        sort=True,
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Representa el %{percentParent:.1%} de su categoría<extra></extra>"
    )
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))
    return fig