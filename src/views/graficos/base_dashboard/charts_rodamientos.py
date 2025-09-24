import plotly.graph_objects as go
import plotly.express as px

COLOR_TEXTO = '#EAEAEA'

def create_recaudo_donut_chart(conteo_estados, estado_seleccionado="TODOS"):
    """Versión OPTIMIZADA: Recibe datos pre-calculados."""
    if conteo_estados is None:
        return None

    colores = {'PAGO': '#28a745', 'SIN PAGO': '#dc3545'}
    
    if estado_seleccionado == "TODOS":
        labels = ['PAGO', 'SIN PAGO']
        values = [conteo_estados.get('PAGO', 0), conteo_estados.get('SIN PAGO', 0)]
        if sum(values) == 0: return None
        total_creditos_str = f"<b>{int(sum(values)):,}</b><br>Créditos Totales"
        titulo_texto = '<b>Estado de Cumplimiento</b>'
        show_legend = True
    else:
        cantidad = conteo_estados.get(estado_seleccionado, 0)
        if cantidad == 0: return None
        labels = [estado_seleccionado]
        values = [cantidad]
        total_creditos_str = f"<b>{int(cantidad):,}</b><br>Créditos Seleccionados"
        titulo_texto = f"<b>Créditos en Estado '{estado_seleccionado.capitalize()}'</b>"
        show_legend = False

    marker_colors = [colores.get(label) for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=.7,
        marker=dict(colors=marker_colors, line=dict(color='#2B2B2B', width=3)),
        textinfo='percent', textfont=dict(size=16, color='white'),
        hoverinfo='none', sort=False,
        hovertemplate="<b>%{label}</b><br><b>Créditos:</b> %{value:,}<br><b>Porcentaje:</b> %{percent}<extra></extra>"
    )])
    fig.update_layout(
        title=dict(text=titulo_texto, font=dict(size=20, color=COLOR_TEXTO), x=0.5),
        annotations=[dict(text=total_creditos_str, x=0.5, y=0.5, font_size=24, showarrow=False, font=dict(color=COLOR_TEXTO))],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=14, color=COLOR_TEXTO)),
        margin=dict(l=20, r=20, t=60, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=show_legend
    )
    return fig

def create_gestion_sunburst_chart(grouped_data, conteo_gestion):
    """Versión OPTIMIZADA: Recibe datos pre-calculados."""
    if grouped_data is None:
        return None
        
    labels = ['CON GESTIÓN', 'SIN GESTIÓN']
    parents = ['', '']
    values = [conteo_gestion.get('CON GESTIÓN', 0), conteo_gestion.get('SIN GESTIÓN', 0)]
    
    hijos = grouped_data[grouped_data['Estado_Gestion'] == 'CON GESTIÓN']
    labels.extend(hijos['Cargo_Usuario'])
    parents.extend(hijos['Estado_Gestion'])
    values.extend(hijos['Cantidad'])

    color_map = {'SIN GESTIÓN': '#dc3545', 'CON GESTIÓN': '#28a745'}
    palette = px.colors.qualitative.Plotly
    cargos_unicos = hijos['Cargo_Usuario'].unique()
    for i, cargo in enumerate(cargos_unicos):
        color_map[cargo] = palette[i % len(palette)]
    final_colors = [color_map.get(label, '#cccccc') for label in labels]

    fig = go.Figure(go.Sunburst(
        labels=labels, parents=parents, values=values,
        branchvalues='total',
        hovertemplate='<b>%{label}</b><br>Créditos: %{value}<br>Del total: %{percentRoot:.2%}',
        marker=dict(colors=final_colors),
        insidetextfont=dict(size=12, color='white')
    ))
    fig.update_layout(
        title=dict(text='<b>Distribución de la Gestión</b>', font=dict(size=20, color=COLOR_TEXTO), x=0.5),
        margin=dict(t=60, l=20, r=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def create_recaudo_detail_sunburst_chart(grouped_data, conteo_gestion, estado_seleccionado):
    """Versión OPTIMIZADA: Reutiliza la lógica y datos pre-calculados."""
    if grouped_data is None:
        return None

    fig = create_gestion_sunburst_chart(grouped_data, conteo_gestion)
    if fig is None: return None

    if estado_seleccionado == 'TODOS':
        titulo = '<b>Detalle de Gestión (General)</b>'
    else:
        titulo = f"<b>Detalle para '{estado_seleccionado.capitalize()}'</b>"

    fig.update_layout(title=dict(text=titulo, font=dict(size=20, color=COLOR_TEXTO), x=0.5))
    return fig

def create_rodamiento_bar_chart(df_agg):
    """
    Versión OPTIMIZADA: Recibe datos pre-agregados y solo los visualiza.
    """
    if df_agg is None or df_agg.empty:
        return None
    
    # <-- YA NO HAY PROCESAMIENTO DE DATOS AQUÍ
    fig = px.bar(
        df_agg,
        x='Rodamiento',
        y='Número de Cuentas',
        color='Franja_Cartera',
        title="<b>Cuentas por Rodamiento y Franja</b>",
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig.update_layout(
        barmode='stack',
        title_font_color='#EAEAEA',
        xaxis_title="Estado de Rodamiento",
        yaxis_title="Número de Cuentas",
        font_color='#EAEAEA',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_title_text='Franja',
        showlegend=True
    )
    fig.update_traces(
        textfont_size=12, textangle=0, textposition='inside', insidetextanchor='middle'
    )
    return fig