import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def create_cumplimiento_bar_chart(df_raw):
    """Crea y devuelve un gráfico de barras de cumplimiento de Call Center."""
    if df_raw.empty:
        return None
    
    df_chart = df_raw.sort_values(by='CALL_CENTER', ascending=False).copy()
    
    # Texto para mostrar EN la barra (ej: 13,07%)
    df_chart['texto_cumplimiento'] = (df_chart['Cumplimiento'] * 100).map('{:.2f}%'.format).str.replace('.', ',')
    
    # NUEVO: Texto específico para el HOVER (solo el número con coma: 13,07)
    df_chart['hover_value'] = (df_chart['Cumplimiento'] * 100).map('{:.2f}'.format).str.replace('.', ',')

    # Asegurar que las columnas existan para evitar errores si el servicio falla
    if 'NOMBRE' not in df_chart.columns: df_chart['NOMBRE'] = 'Sin Nombre'
    if 'Franja' not in df_chart.columns: df_chart['Franja'] = 'N/A'

    fig_bar = px.bar(
        df_chart, 
        x='Cumplimiento', 
        y='CALL_CENTER', 
        orientation='h', 
        text='texto_cumplimiento',
        # Pasamos las columnas extras que queremos mostrar en el tooltip
        custom_data=['NOMBRE', 'Franja', 'hover_value'], 
        labels={'CALL_CENTER': 'Call Center', 'Cumplimiento': 'Porcentaje de Cumplimiento'}
    )
    
    fig_bar.update_layout(
        xaxis_tickformat='.0%', 
        yaxis_title=None, 
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    # ACTUALIZACIÓN DEL TOOLTIP (HOVERTEMPLATE)
    fig_bar.update_traces(
        textposition='auto', 
        marker_color='#1f77b4',
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "Nombre: %{customdata[0]}<br>" +
            "Franja: %{customdata[1]}<br>" +
            "Porcentaje: %{customdata[2]}%<extra></extra>"
        )
    )
    return fig_bar

def create_rodamiento_pie_chart(df_rodamiento_count):
    """Crea y devuelve un gráfico de torta de rodamientos."""
    if df_rodamiento_count.empty:
        return None
    fig_pie = px.pie(
        df_rodamiento_count,
        names='Rodamiento',
        values='count',
    )
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent'
    )
    fig_pie.update_layout(
        showlegend=True,
        legend_title_text='Rodamiento',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig_pie

def create_styled_summary_table(df_raw, style_function, expected_compliance):
    """Crea y devuelve el HTML de una tabla de resumen con estilos."""
    if df_raw.empty:
        return ""  
    df_styled = df_raw.copy()
    df_styled = df_styled.rename(columns={
        'META_$': 'Meta ($)', 'Recaudo_Meta': 'Recaudo ($)', 'Cumplimiento': 'Cumplimiento (%)',
        'NOMBRE': 'Nombre', 'Faltante': 'Faltante ($)'
    })
    column_order = ['CALL_CENTER', 'Nombre', 'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)']
    
    # Asegurar que todas las columnas existan antes de filtrar
    existing_cols = [col for col in column_order if col in df_styled.columns]
    df_styled = df_styled[existing_cols]
    
    styled_df = df_styled.style.map(
        lambda x: style_function(x, expected_compliance),
        subset=['Cumplimiento (%)']
    ).format({
        'Meta ($)': '${:,.0f}', 'Recaudo ($)': '${:,.0f}', 'Faltante ($)': '${:,.0f}',
        'Cumplimiento (%)': '{:.2%}'
    }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
        {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
    ])
    return styled_df.to_html()

def create_estado_llamadas_bar_chart(df_grafico_llamadas):
    """
    Crea un gráfico de barras para "CON RESPUESTA" vs "SIN RESPUESTA".
    """
    if df_grafico_llamadas.empty:
        return None
    # Formatear el número con punto de mil
    df_grafico_llamadas['Texto'] = df_grafico_llamadas['Cantidad'].apply(lambda x: f'{x:,.0f}'.replace(',', '.'))

    fig = px.bar(
        df_grafico_llamadas,
        x='Tipo',
        y='Cantidad',
        title='Gestión de Llamadas',
        text='Texto', # Usar la columna formateada para el texto
        labels={'Tipo': '', 'Cantidad': 'Número de Llamadas'}
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Cantidad de Llamadas",
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    fig.update_traces(
        textposition='outside',
        marker_color='#004A99' # Un color azul corporativo
    )
    return fig

def create_efectividad_call_chart(df_efectividad):
    """
    Crea un gráfico de barras horizontales que muestra la efectividad de
    llamadas por Call Center.
    """
    if df_efectividad.empty:
        return None

    # Asegurarse de que las columnas necesarias existen
    cols_necesarias = ['Call_Center', 'Efectividad', 'Con_Respuesta', 'Total_Intentos']
    if not all(col in df_efectividad.columns for col in cols_necesarias):
        print(f"Error: Faltan columnas clave. Se necesitan: {cols_necesarias}")
        return None

    df_chart = df_efectividad.sort_values(by='Efectividad', ascending=True).reset_index(drop=True)

    # --- 1. Formateo de Texto ---
    def format_text_efectividad(row):
        pct = f"{row['Efectividad']:.2%}".replace('.', ',')
        count = f"{row['Con_Respuesta']:,.0f}".replace(',', '.')
        return f"<b>{pct}</b> ({count})"
        
    df_chart['Texto_Efectividad'] = df_chart.apply(format_text_efectividad, axis=1)

    def format_text_total(row):
        total = f"{row['Total_Intentos']:,.0f}".replace(',', '.')
        return f"<b>{total}</b>"
        
    df_chart['Texto_Total'] = df_chart.apply(format_text_total, axis=1)

    # --- 2. Lógica de posicionamiento y color ---
    umbral_colision = 0.85 
    
    df_chart['text_position'] = df_chart['Efectividad'].apply(
        lambda x: 'inside' if x > umbral_colision else 'outside'
    )
    df_chart['text_color'] = df_chart['Efectividad'].apply(
        lambda x: 'white' if x > umbral_colision else '#333333'
    )

    # --- 3. Estilos para las barras ---
    bar_thickness = 0.5 
    border_radius = 15 

    # --- 4. Crear la figura base ---
    fig = go.Figure()

    # --- 5. Barra de fondo (gris) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=[1] * len(df_chart),
        orientation='h',
        width=bar_thickness,
        marker=dict(
            color='rgba(230, 230, 230, 0.9)', 
            cornerradius=border_radius
        ), 
        hoverinfo='none',
        showlegend=False
    ))

    # --- 6. Barra de efectividad (azul) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=df_chart['Efectividad'],
        orientation='h',
        width=bar_thickness,
        marker=dict(
            color='#3366CC',
            cornerradius=border_radius
        ), 
        hoverinfo='none',
        showlegend=False,
        text=df_chart['Texto_Efectividad'],
        textposition=df_chart['text_position'], 
        textfont=dict(
            color=df_chart['text_color'], 
            size=11,
            family="Arial, sans-serif"
        ),
        insidetextanchor='end' 
    ))

    # --- 7. Configurar el layout ---
    fig.update_layout(
        title_text='% = Llamadas con respuesta / Total de intentos',
        title_x=0.05, 
        title_font_size=14,
        title_font_family="Arial, sans-serif",
        barmode='overlay',
        bargap=0,        
        bargroupgap=0, 
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0, 1.4],
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(size=12, color='#333333'),
            categoryorder='array',
            categoryarray=df_chart['Call_Center']
        ),
        yaxis_title=None,
        margin=dict(l=50, r=80, t=50, b=5), 
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450 
    )
    
    # --- 8. Añadir el texto del 'Total_Intentos' usando anotaciones ---
    for i, row in df_chart.iterrows():
        fig.add_annotation(
            x=1.03, 
            y=row['Call_Center'], 
            text=row['Texto_Total'],
            showarrow=False,
            font=dict(size=11, color='#333333', family="Arial, sans-serif"),
            xanchor='left', 
            yanchor='middle'
        )
    
    return fig

def create_llamadas_por_dia_area_chart(df_llamadas_dia, filtros_respuesta: list, alerta_umbral: int):
    """
    Crea un gráfico de área suavizada (Spline) moderno para la tendencia de llamadas
    CON ETIQUETAS DE DATOS (Cantidades visibles).
    """
    if df_llamadas_dia.empty:
        return None
    
    # 1. Filtrado de Datos
    if not filtros_respuesta:
        df_filtrado_agg = pd.DataFrame(columns=['Fecha', 'Total_Llamadas'])
        title_str = "NINGUNO"
    else:
        df_filtrado = df_llamadas_dia[df_llamadas_dia['Estado_Respuesta'].isin(filtros_respuesta)].copy()
        df_filtrado_agg = df_filtrado.groupby('Fecha')['Total_Llamadas'].sum().reset_index()
        
        if len(filtros_respuesta) > 1:
            title_str = "TODAS"
        else:
            title_str = filtros_respuesta[0]
            
    if df_filtrado_agg.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False}, yaxis={"visible": False},
            annotations=[{
                "text": "No hay datos para mostrar con los filtros actuales",
                "xref": "paper", "yref": "paper", "showarrow": False,
                "font": {"size": 16, "color": "#888"}
            }],
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    df_filtrado_agg.sort_values(by='Fecha', inplace=True)
    
    # --- COLORES Y ESTILOS ---
    LINE_COLOR = '#3366CC'       
    FILL_COLOR = 'rgba(51, 102, 204, 0.2)' 
    MARKER_COLOR = '#FFFFFF'     
    ALERT_COLOR = '#FF4B4B'      
    
    # 1. Texto para el Tooltip (Hover) - Detallado
    df_filtrado_agg['Hover_Text'] = df_filtrado_agg.apply(
        lambda row: f"<b>{row['Fecha']:%d %b}</b><br>Llamadas: <b>{row['Total_Llamadas']:,.0f}</b>".replace(',', '.'),
        axis=1
    )

    # 2. Texto para la Etiqueta (Label) - Solo el número
    df_filtrado_agg['Label_Text'] = df_filtrado_agg['Total_Llamadas'].apply(
        lambda x: f"{x:,.0f}".replace(',', '.')
    )

    fig = go.Figure()

    # --- TRACE PRINCIPAL ---
    fig.add_trace(go.Scatter(
        x=df_filtrado_agg['Fecha'],
        y=df_filtrado_agg['Total_Llamadas'],
        mode='lines+markers+text', # <--- AGREGADO '+text'
        
        # Configuración de la Línea y Área
        line=dict(color=LINE_COLOR, width=3, shape='spline', smoothing=1.3),
        fill='tozeroy',
        fillcolor=FILL_COLOR,
        
        # Configuración del Marcador (Punto)
        marker=dict(
            size=9, 
            color=MARKER_COLOR, 
            line=dict(width=2, color=LINE_COLOR)
        ),
        
        # Configuración de la Etiqueta (Texto visible)
        text=df_filtrado_agg['Label_Text'], # Muestra solo el número
        textposition="top center",          # Ubicación encima del punto
        textfont=dict(
            size=11, 
            color=LINE_COLOR,               # Mismo color que la línea para elegancia
            family="Arial, sans-serif",
            weight="bold"                   # Negrita para que se lea bien
        ),
        cliponaxis=False,                   # Permite que el texto se salga un poco del margen superior si es necesario
        
        # Configuración del Hover (Tooltip)
        name='Llamadas',
        customdata=df_filtrado_agg['Hover_Text'], # Pasamos el texto rico a customdata
        hovertemplate="%{customdata}<extra></extra>" # Usamos customdata para el hover
    ))

    # --- LÍNEA DE ALERTA ---
    if alerta_umbral > 0:
        fig.add_hline(
            y=alerta_umbral, 
            line_dash="dash", 
            line_color=ALERT_COLOR, 
            line_width=1.5,
            annotation_text=f"Meta ({alerta_umbral})", 
            annotation_position="bottom right",
            annotation_font=dict(color=ALERT_COLOR, size=10)
        )
        
        # Puntos de Alerta
        df_alerta = df_filtrado_agg[df_filtrado_agg['Total_Llamadas'] <= alerta_umbral].copy()
        if not df_alerta.empty:
            fig.add_trace(go.Scatter(
                x=df_alerta['Fecha'],
                y=df_alerta['Total_Llamadas'],
                mode='markers+text', # También mostramos texto en las alertas
                marker=dict(color=ALERT_COLOR, size=10, symbol='circle'),
                text=df_alerta['Label_Text'],
                textposition="bottom center", # Texto abajo para diferenciarlo
                textfont=dict(size=11, color=ALERT_COLOR, weight="bold"),
                name='Bajo Rendimiento',
                hoverinfo='skip' 
            ))

    # --- LAYOUT ---
    fig.update_layout(
        title=dict(
            text=f"Evolución Diaria de Llamadas ({title_str})",
            font=dict(size=18, color='#333333'),
            x=0,
        ),
        xaxis=dict(
            showgrid=False,
            tickformat='%d %b',
            tickfont=dict(color='#666'),
            linecolor='#ddd',
            showspikes=True,
            spikethickness=1,
            spikedash='dot',
            spikecolor='#999',
            spikemode='across'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            zeroline=False,
            tickfont=dict(color='#666'),
            # Añadimos un poco de margen automático arriba para que quepan los números
            automargin=True 
        ),
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, color='#555')
        ),
        height=400
    )

    return fig

def create_mensajeria_funnel_chart(df_funnel):
    """
    Crea un gráfico de embudo (funnel chart) para la gestión de mensajería.
    """
    if df_funnel.empty:
        return None
    
    df_chart = df_funnel.copy()
    
    # Aseguramos que 'Gestión en Sistema' tenga tilde para coincidir con el servicio
    df_chart['Etapa_Orden'] = df_chart['Etapa'].map({
        'Mensajes Entregados': 4,
        'Conversaciones': 3,
        'Gestión en Sistema': 2, 
        'Clientes con Pago': 1
    })
    
    # Ordenamos explícitamente usando esta columna auxiliar
    df_chart = df_chart.sort_values(by='Etapa_Orden', ascending=False) 

    fig = go.Figure(go.Funnel(
        y = df_chart['Etapa'], 
        x = df_chart['Cantidad'], 
        textinfo = "value", 
        textfont = dict(color='white', size=14), 
        marker = dict(color="#6A5ACD"), 
        connector = dict(line=dict(color="white", dash="dot", width=1)), 
        opacity = 0.8 
    ))
    
    fig.update_layout(
        yaxis_title=None,
        xaxis=dict(visible=False), 
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(color='black') # O ajusta a 'white' si tu fondo es oscuro
    )
    
    return fig

def create_efectividad_mensajeria_chart(df_efectividad):
    """
    Crea un gráfico de barras horizontales que muestra la efectividad de
    mensajería (Conversaciones / Entregados) por Call Center.
    """
    if df_efectividad.empty:
        return None
    
    cols_necesarias = ['Call_Center', 'Efectividad', 'Total_Conversaciones', 'Total_Entregados']
    if not all(col in df_efectividad.columns for col in cols_necesarias):
         print(f"Error: Faltan columnas clave. Se necesitan: {cols_necesarias}")
         return None

    df_chart = df_efectividad.sort_values(by='Efectividad', ascending=True).reset_index(drop=True)

    # --- 1. Formateo de Texto ---
    def format_text_efectividad(row):
        pct = f"{row['Efectividad']:.2%}".replace('.', ',')
        count = f"{row['Total_Conversaciones']:,.0f}".replace(',', '.')
        return f"<b>{pct}</b> ({count})"
        
    df_chart['Texto_Efectividad'] = df_chart.apply(format_text_efectividad, axis=1)

    def format_text_total(row):
        total = f"{row['Total_Entregados']:,.0f}".replace(',', '.')
        return f"<b>{total}</b>"
        
    df_chart['Texto_Total'] = df_chart.apply(format_text_total, axis=1)

    # --- 2. Lógica de posicionamiento y color ---
    umbral_colision = 0.85 
    
    df_chart['text_position'] = df_chart['Efectividad'].apply(
        lambda x: 'inside' if x > umbral_colision else 'outside'
    )
    df_chart['text_color'] = df_chart['Efectividad'].apply(
        lambda x: 'white' if x > umbral_colision else '#333333'
    )

    # --- 3. Estilos de barra ---
    bar_thickness = 0.5
    border_radius_px = 15

    # --- 4. Crear la figura base ---
    fig = go.Figure()

    # --- 5. Barra de fondo (gris) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=[1] * len(df_chart),
        orientation='h',
        width=bar_thickness, 
        marker=dict(
            color='rgba(230, 230, 230, 0.9)', 
            cornerradius=border_radius_px 
        ), 
        hoverinfo='none',
        showlegend=False
    ))

    # --- 6. Barra de efectividad (azul) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=df_chart['Efectividad'],
        orientation='h',
        width=bar_thickness, 
        marker=dict(
            color='#3366CC',
            cornerradius=border_radius_px 
        ), 
        hoverinfo='none',
        showlegend=False,
        text=df_chart['Texto_Efectividad'],
        textposition=df_chart['text_position'], 
        textfont=dict(
            color=df_chart['text_color'], 
            size=11,
            family="Arial, sans-serif"
        ),
        insidetextanchor='end' 
    ))

    # --- 7. Configurar el layout ---
    fig.update_layout(
        title_text='% = Conversaciones / Mensajes Entregados',
        title_x=0.05, 
        title_font_size=14,
        title_font_family="Arial, sans-serif",
        barmode='overlay',
        bargap=0, 
        bargroupgap=0, 
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0, 1.4],
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(size=12, color='#333333'),
            categoryorder='array',
            categoryarray=df_chart['Call_Center']
        ),
        yaxis_title=None,
        margin=dict(l=50, r=80, t=50, b=20), 
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400 
    )
    
    # --- 8. Añadir el texto del 'Total_Entregados' usando anotaciones ---
    for i, row in df_chart.iterrows():
        fig.add_annotation(
            x=1.03, 
            y=row['Call_Center'], 
            text=row['Texto_Total'],
            showarrow=False,
            font=dict(size=11, color='#333333', family="Arial, sans-serif"),
            xanchor='left', 
            yanchor='middle'
        )
    
    return fig

# --- NUEVA FUNCIÓN PARA EL DONUT CHART ---

def create_gestion_donut_chart(df_cartera):
    """
    Crea un gráfico de dona mostrando la proporción de 
    CON GESTIÓN vs SIN GESTIÓN para los Call Centers.
    """
    if df_cartera.empty or 'Estado_Gestion' not in df_cartera.columns:
        return None

    # Agrupar datos
    conteo = df_cartera['Estado_Gestion'].value_counts().reset_index()
    conteo.columns = ['Estado', 'Cantidad']

    # Definir colores (Verde para gestión, Rojo/Gris para sin gestión)
    color_map = {
        'CON GESTIÓN': '#2ECC71',  # Verde
        'SIN GESTIÓN': '#E74C3C',  # Rojo
        'SIN DATO': '#95A5A6'
    }

    fig = px.pie(
        conteo,
        values='Cantidad',
        names='Estado',
        hole=0.5, # Esto lo hace una dona
        color='Estado',
        color_discrete_map=color_map
    )

    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>"
    )

    fig.update_layout(
        title_text="Cobertura de Gestión",
        title_x=0.5,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    
    # Añadir texto en el centro con el total
    total_creditos = conteo['Cantidad'].sum()
    fig.add_annotation(
        text=f"<b>{total_creditos}</b><br>Créditos",
        x=0.5, y=0.5,
        showarrow=False,
        font_size=14,
        font_color="#333"
    )

    return fig

def create_tipo_novedad_donut_chart(df_cartera):
    """
    Crea un gráfico de dona mostrando la distribución de 'Tipo_Novedad'
    EXCLUSIVAMENTE para los créditos que tienen 'CON GESTIÓN'.
    """
    if df_cartera.empty or 'Estado_Gestion' not in df_cartera.columns or 'Tipo_Novedad' not in df_cartera.columns:
        return None

    # 1. Filtrar solo los que tienen gestión
    df_gestionados = df_cartera[df_cartera['Estado_Gestion'] == 'CON GESTIÓN'].copy()

    if df_gestionados.empty:
        return None

    # 2. Agrupar por Tipo de Novedad
    # Rellenar nulos por si acaso
    df_gestionados['Tipo_Novedad'] = df_gestionados['Tipo_Novedad'].fillna('SIN CLASIFICAR')
    conteo = df_gestionados['Tipo_Novedad'].value_counts().reset_index()
    conteo.columns = ['Tipo', 'Cantidad']

    # 3. Crear el gráfico
    fig = px.pie(
        conteo,
        values='Cantidad',
        names='Tipo',
        hole=0.5,
        color='Tipo',
        # Plotly asignará colores automáticos, pero puedes definir un mapa si quieres colores fijos
    )

    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>"
    )

    fig.update_layout(
        title_text="Distribución por Tipo de Novedad",
        title_x=0.5,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1), # Leyenda abajo horizontal
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    
    # Texto central con el total de gestionados
    total_gestionados = conteo['Cantidad'].sum()
    fig.add_annotation(
        text=f"<b>{total_gestionados}</b><br>Gestionados",
        x=0.5, y=0.5,
        showarrow=False,
        font_size=13,
        font_color="#333"
    )
    return fig

def create_compromisos_stacked_bar_chart(df_compromisos):
    """
    Gráfico de barras apiladas con 3 categorías: Vigentes, Vencidos y Sin Fecha.
    """
    if df_compromisos.empty:
        return None
    
    # 1. Definir Colores (3 Categorías)
    color_map = {
        'ACUERDOS VIGENTES': '#0B5375',   # Azul Oscuro
        'ACUERDOS VENCIDOS': '#85929E',   # Gris Azulado
        'ACUERDOS SIN FECHA': '#E59866'   # Naranja Suave (Alerta visual pero no agresiva)
    }
    
    # 2. Crear Gráfico
    fig = px.bar(
        df_compromisos,
        x="Cantidad",
        y="Call_Center_Asignado",
        color="Estado_Acuerdo",
        orientation='h',
        text="Cantidad",
        color_discrete_map=color_map,
        # Orden Lógico: Vigentes primero, luego Vencidos, luego los Errores
        category_orders={"Estado_Acuerdo": ["ACUERDOS VIGENTES", "ACUERDOS VENCIDOS", "ACUERDOS SIN FECHA"]}
    )
    
    # 3. Diseño
    fig.update_layout(
        title_text="Estado de Compromisos de Pago",
        title_x=0,
        xaxis_title=None,
        yaxis_title=None,
        legend_title_text=None,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_traces(
        textposition='inside',
        textfont=dict(color='white', size=12)
    )
    
    return fig