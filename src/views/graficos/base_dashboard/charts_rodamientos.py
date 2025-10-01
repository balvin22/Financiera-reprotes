import plotly.graph_objects as go
import plotly.express as px

COLOR_TEXTO = '#EAEAEA'

def create_recaudo_donut_chart(conteo_estados, estado_seleccionado="TODOS", show_center_text=True):
    """Crea el gráfico de dona principal para PAGO vs SIN PAGO."""
    if conteo_estados is None:
        return None

    colores = {'PAGO': '#28a745', 'SIN PAGO': '#dc3545'}

    if estado_seleccionado == "TODOS":
        labels = ['PAGO', 'SIN PAGO']
        values = [conteo_estados.get('PAGO', 0), conteo_estados.get('SIN PAGO', 0)]
        if sum(values) == 0: return None
        total_creditos_str = f"<b>{int(sum(values)):,}</b><br>Créditos Totales"
        show_legend = True
    else:
        cantidad = conteo_estados.get(estado_seleccionado, 0)
        if cantidad == 0: return None
        labels = [estado_seleccionado]
        values = [cantidad]
        total_creditos_str = f"<b>{int(cantidad):,}</b><br>Créditos Seleccionados"
        show_legend = False

    marker_colors = [colores.get(label) for label in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=.7,
        marker=dict(colors=marker_colors, line=dict(color='#2B2B2B', width=3)),
        textinfo='percent', textfont=dict(size=16, color='white'),
        hoverinfo='none', sort=False,
        hovertemplate="<b>%{label}</b><br><b>Créditos:</b> %{value:,}<br><b>Porcentaje:</b> %{percent}<extra></extra>"
    )])

    annotations = []
    if show_center_text:
        annotations.append(dict(text=total_creditos_str, x=0.5, y=0.5, font_size=24, showarrow=False, font=dict(color=COLOR_TEXTO)))

    fig.update_layout(
        annotations=annotations,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=14, color=COLOR_TEXTO)),
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=show_legend
    )
    return fig


def create_nested_pie_chart(grouped_data, conteo_gestion, height=300):
    """
    Crea un gráfico de anillos anidados (Nested Pie Chart) visualmente atractivo.
    Es un reemplazo estético para el sunburst chart.
    """
    if grouped_data is None or conteo_gestion is None:
        return None

    # --- 1. Definir la estructura de datos (igual que en el sunburst) ---
    labels = ['CON GESTIÓN', 'SIN GESTIÓN']
    parents = ['', '']
    values = [conteo_gestion.get('CON GESTIÓN', 0), conteo_gestion.get('SIN GESTIÓN', 0)]

    hijos = grouped_data[grouped_data['Estado_Gestion'] == 'CON GESTIÓN']
    labels.extend(hijos['Cargo_Usuario'])
    parents.extend(['CON GESTIÓN'] * len(hijos))
    values.extend(hijos['Cantidad'])

    # --- 2. La Magia Visual: Paleta de Colores Armónica ---
    color_map = {
        'SIN GESTIÓN': '#FF6B6B',  # Un rojo más suave
        'CON GESTIÓN': '#1DDBA4'    # Un verde azulado (teal) moderno
    }
    child_colors = px.colors.sequential.Tealgrn
    cargos_unicos = hijos['Cargo_Usuario'].unique()
    for i, cargo in enumerate(cargos_unicos):
        color_map[cargo] = child_colors[i % len(child_colors)]

    # --- 3. Construir el Gráfico ---
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues='total',
        hovertemplate='<b>%{label}</b><br>Créditos: %{value}<br>Del total: %{percentRoot:.2%}<extra></extra>',
        marker=dict(colors=[color_map.get(l) for l in labels]),
        insidetextorientation='radial',
        textinfo='label+percent parent'
    ))

    # --- 4. Ajustes Finales de Estilo ---
    fig.update_layout(
        height=height,
        margin=dict(t=5, l=10, r=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig


def create_gestion_sunburst_chart(grouped_data, conteo_gestion, height=100):
    """
    MODIFICADO: Ahora simplemente llama a nuestra nueva función de gráfico mejorada.
    Mantenemos el nombre para máxima compatibilidad con tu código existente.
    """
    return create_nested_pie_chart(grouped_data, conteo_gestion, height)

def create_recaudo_detail_sunburst_chart(grouped_data, conteo_gestion, estado_seleccionado, height=100):
    """
    MODIFICADO: Esta también llama a la nueva función de gráfico.
    """
    return create_nested_pie_chart(grouped_data, conteo_gestion, height)

def create_rodamiento_bar_chart(df_agg):
    """
    Versión OPTIMIZADA: Recibe datos pre-agregados y solo los visualiza.
    """
    if df_agg is None or df_agg.empty:
        return None
    
    fig = px.bar(
        df_agg,
        x='Rodamiento',
        y='Número de Cuentas',
        # <-- CAMBIO: El color ahora se basa en el estado de la gestión
        color='Estado_Gestion', 
        title="<b>Cuentas por Rodamiento y Estado de Gestión</b>", 
        text_auto=True,
        color_discrete_map={
            'CON GESTIÓN': '#1f77b4',  # Azul
            'SIN GESTIÓN': '#d62728'   # Rojo
        }
    )
    fig.update_layout(
        barmode='stack',
        title_font_color='#EAEAEA',
        xaxis_title="Estado de Rodamiento",
        yaxis_title="Número de Cuentas",
        font_color='#EAEAEA',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_title_text='Gestión', 
        showlegend=True
    )
    fig.update_traces(
        textfont_size=12, textangle=0, textposition='inside', insidetextanchor='middle'
    )
    return fig