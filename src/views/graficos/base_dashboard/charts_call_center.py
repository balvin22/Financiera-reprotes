import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def create_cumplimiento_bar_chart(df_raw):
    """Crea y devuelve un gráfico de barras de cumplimiento de Call Center."""
    if df_raw.empty:
        return None
    df_chart = df_raw.sort_values(by='CALL_CENTER', ascending=False).copy()
    df_chart['texto_cumplimiento'] = (df_chart['Cumplimiento'] * 100).map('{:.2f}%'.format).str.replace('.', ',')

    fig_bar = px.bar(
        df_chart, x='Cumplimiento', y='CALL_CENTER', orientation='h', text='texto_cumplimiento',
        labels={'CALL_CENTER': 'Call Center', 'Cumplimiento': 'Porcentaje de Cumplimiento'}
    )
    fig_bar.update_layout(xaxis_tickformat='.0%', yaxis_title=None, margin=dict(l=20, r=20, t=40, b=20))
    fig_bar.update_traces(textposition='auto', marker_color='#1f77b4')
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
    df_styled = df_styled[column_order]
    
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
    llamadas por Call Center, con barras estilizadas (finas y redondeadas).

    [CAMBIO]: El texto de efectividad se mueve DENTRO de la barra (color blanco)
    si la efectividad supera el 90% para evitar colisiones.
    
    [CAMBIO]: Se usa un estilo de barras redondeadas unificado.
    
    [CAMBIO]: Se usan Anotaciones para el texto del Total para un control preciso.
    """
    if df_efectividad.empty:
        return None

    # Asegurarse de que las columnas necesarias existen
    cols_necesarias = ['Call_Center', 'Efectividad', 'Con_Respuesta', 'Total_Intentos']
    if not all(col in df_efectividad.columns for col in cols_necesarias):
        print(f"Error: Faltan columnas clave. Se necesitan: {cols_necesarias}")
        return None

    # [CAMBIO]: Ordenar y resetear el índice para que las anotaciones funcionen
    df_chart = df_efectividad.sort_values(by='Efectividad', ascending=True).reset_index(drop=True)

    # --- 1. Formateo de Texto (como lo tenías) ---
    def format_text_efectividad(row):
        pct = f"{row['Efectividad']:.2%}".replace('.', ',')
        count = f"{row['Con_Respuesta']:,.0f}".replace(',', '.')
        return f"<b>{pct}</b> ({count})"
        
    df_chart['Texto_Efectividad'] = df_chart.apply(format_text_efectividad, axis=1)

    def format_text_total(row):
        total = f"{row['Total_Intentos']:,.0f}".replace(',', '.')
        return f"<b>{total}</b>"
        
    df_chart['Texto_Total'] = df_chart.apply(format_text_total, axis=1)

    # --- 2. [NUEVO] Lógica de posicionamiento y color ---
    # Define un umbral. Si es > 85%, el texto va adentro.
    umbral_colision = 0.85 
    
    df_chart['text_position'] = df_chart['Efectividad'].apply(
        lambda x: 'inside' if x > umbral_colision else 'outside'
    )
    df_chart['text_color'] = df_chart['Efectividad'].apply(
        lambda x: 'white' if x > umbral_colision else '#333333'
    )

    # --- 3. Estilos para las barras (tus valores) ---
    bar_thickness = 0.5  # Controla qué tan "finita" es la barra
    border_radius = 15   # Controla el redondeo de las esquinas

    # --- 4. Crear la figura base ---
    fig = go.Figure()

    # --- 5. Barra de fondo (gris) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=[1] * len(df_chart), # Barra al 100%
        orientation='h',
        width=bar_thickness,
        marker=dict(
            color='rgba(230, 230, 230, 0.9)', 
            cornerradius=border_radius # <-- [CAMBIO] Redondeo completo
        ), 
        hoverinfo='none',
        showlegend=False
        # [CAMBIO]: Quitamos el texto de aquí. Usaremos anotaciones.
    ))

    # --- 6. Barra de efectividad (azul) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=df_chart['Efectividad'],
        orientation='h',
        width=bar_thickness,
        marker=dict(
            color='#3366CC',
            cornerradius=border_radius # <-- [CAMBIO] Redondeo completo
        ), 
        hoverinfo='none',
        showlegend=False,
        text=df_chart['Texto_Efectividad'],
        
        # --- [CAMBIO CLAVE] ---
        # Usa las listas que creamos en Pandas
        textposition=df_chart['text_position'], 
        textfont=dict(
            color=df_chart['text_color'], 
            size=11,
            family="Arial, sans-serif"
        ),
        # Asegura que el texto "inside" se alinee a la derecha
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
            range=[0, 1.4], # Rango amplio para que quepan ambos textos
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(size=12, color='#333333'),
            # [CAMBIO]: Asegurar el orden de las categorías
            categoryorder='array',
            categoryarray=df_chart['Call_Center']
        ),
        yaxis_title=None,
        # [CAMBIO]: Aumentar margen derecho para el texto del total
        margin=dict(l=50, r=80, t=50, b=5), 
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450 # Ajusta la altura si es necesario
    )
    
    # --- 8. [NUEVO] Añadir el texto del 'Total_Intentos' usando anotaciones ---
    for i, row in df_chart.iterrows():
        fig.add_annotation(
            x=1.03, # Posición X fija (un poco más allá del 100%)
            y=row['Call_Center'], # Posición Y basada en la categoría
            text=row['Texto_Total'],
            showarrow=False,
            font=dict(size=11, color='#333333', family="Arial, sans-serif"),
            xanchor='left', # Anclar el texto a la izquierda de la posición X
            yanchor='middle'
        )
    
    return fig

def create_llamadas_por_dia_area_chart(df_llamadas_dia, filtros_respuesta: list, alerta_umbral: int):
    """
    Crea un gráfico de área que muestra la tendencia de llamadas por día,
    filtrado por una lista de estados de respuesta ('CON RESPUESTA', 'SIN RESPUESTA').
    Se aplica un estilo oscuro similar al de la imagen de ejemplo.
    """
    if df_llamadas_dia.empty:
        return None
    
    # --- (Lógica de filtrado y título - SIN CAMBIOS) ---
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
    
    # --- (Colores - SIN CAMBIOS) ---
    BG_COLOR = '#3d3d3d'
    GRID_COLOR = 'rgba(255, 255, 255, 0.2)'
    LINE_COLOR = '#007FFF'
    FILL_COLOR = 'rgba(0, 127, 255, 0.3)'

    if df_filtrado_agg.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"Tendencia de Llamadas (Días Hábiles): {title_str}",
            xaxis_title="Fecha",
            yaxis_title="Total Llamadas",
            plot_bgcolor=BG_COLOR,
            paper_bgcolor=BG_COLOR,
            font_color='white',
            annotations=[{
                "text": "No hay datos para esta selección.",
                "xref": "paper", "yref": "paper",
                "showarrow": False, "font": {"size": 16, "color": "white"}
            }]
        )
        return fig
        
    df_filtrado_agg.sort_values(by='Fecha', inplace=True)
    
    df_filtrado_agg['Texto_Hover'] = df_filtrado_agg.apply(
        lambda row: f"<b>Fecha:</b> {row['Fecha']:%d-%b-%Y}<br><b>Total:</b> {row['Total_Llamadas']:,.0f}".replace(',', '.'),
        axis=1
    )
    
    fig = go.Figure()
    
    # --- (Trace principal - SIN CAMBIOS) ---
    fig.add_trace(go.Scatter(
        x=df_filtrado_agg['Fecha'],
        y=df_filtrado_agg['Total_Llamadas'],
        mode='lines+markers',
        fill='tozeroy',
        marker=dict(color=LINE_COLOR, size=5),
        line=dict(color=LINE_COLOR, width=2),
        fillcolor=FILL_COLOR,
        name=title_str,
        hoverinfo='text',
        text=df_filtrado_agg['Texto_Hover']
    ))
    
    # --- [NUEVO] Añadir línea de alerta y marcadores ---
    if alerta_umbral > 0:
        # 1. Encontrar los puntos que están por debajo del umbral
        df_alerta = df_filtrado_agg[df_filtrado_agg['Total_Llamadas'] <= alerta_umbral].copy()
        
        if not df_alerta.empty:
            # 2. Añadir marcadores 'x' rojos en esos puntos
            fig.add_trace(go.Scatter(
                x=df_alerta['Fecha'],
                y=df_alerta['Total_Llamadas'],
                mode='markers',
                marker=dict(color='red', size=10, symbol='x-thin', line=dict(width=2)),
                name=f'Alerta (<= {alerta_umbral})',
                hoverinfo='none' # No interfiere con el hover principal
            ))

        # 3. Añadir la línea horizontal de alerta
        fig.add_hline(
            y=alerta_umbral, 
            line_dash="dot", 
            line_color="red",
            annotation_text=f"Umbral Alerta ({alerta_umbral})", 
            annotation_position="bottom right",
            annotation_font_color="red"
        )
    # --- [FIN NUEVO] ---

    # --- (Layout - SIN CAMBIOS) ---
    fig.update_layout(
        title=f"Tendencia de Llamadas Diarias (Días Hábiles): {title_str}",
        xaxis_title=None,
        yaxis_title="Total Llamadas",
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        font_color='white',
        xaxis=dict(
            gridcolor=GRID_COLOR, 
            showgrid=False,
            tickformat='%d-%b',
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR, 
            showgrid=True,
            zeroline=False
        ),
        margin=dict(l=50, r=20, t=50, b=20),
        hovermode="x unified",
        legend=dict( # <-- Añadir esto para la leyenda de la alerta
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="white")
        )
    )
    
    return fig

def create_mensajeria_funnel_chart(df_funnel):
    """
    Crea un gráfico de embudo (funnel chart) para la gestión de mensajería,
    con el estilo piramidal de Plotly, similar a la imagen provista.
    """
    if df_funnel.empty:
        return None
    df_chart = df_funnel.copy()
    df_chart['Etapa_Orden'] = df_chart['Etapa'].map({
        'Mensajes Entregados': 4,
        'Conversaciones': 3,
        'Gestion en Sistema': 2,
        'Clientes con Pago': 1
    })
    df_chart = df_chart.sort_values(by='Etapa_Orden', ascending=False) # Ordenar de arriba a abajo

    # Generar el gráfico de embudo
    fig = go.Figure(go.Funnel(
        y = df_chart['Etapa'], # Las etiquetas en el eje Y
        x = df_chart['Cantidad'], # Los valores en el eje X
        textinfo = "value", # Mostrar el valor dentro de cada barra
        textfont = dict(color='white', size=14), # Estilo del texto
        marker = dict(color="#6A5ACD"), # Un color morado similar al de la imagen
        connector = dict(line=dict(color="white", dash="dot", width=1)), # Conectores entre las etapas
        opacity = 0.8 # Ligeramente transparente para un mejor look
    ))
    
    fig.update_layout(
        yaxis_title=None,
        xaxis=dict(visible=False), 
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=20, b=20), # <-- Reduje 't' de 50 a 20
        font=dict(color='black')
    )
    
    return fig

def create_efectividad_mensajeria_chart(df_efectividad):
    """
    Crea un gráfico de barras horizontales que muestra la efectividad de
    mensajería (Conversaciones / Entregados) por Call Center.
    
    [CAMBIO]: El texto de efectividad se mueve DENTRO de la barra (color blanco)
    si la efectividad supera el 90% para evitar colisiones.
    
    [CAMBIO]: Se usa un estilo de barras finas y redondeadas.
    
    [CAMBIO]: Se usan Anotaciones para el texto del Total para un control preciso.
    """
    if df_efectividad.empty:
        return None
    
    cols_necesarias = ['Call_Center', 'Efectividad', 'Total_Conversaciones', 'Total_Entregados']
    if not all(col in df_efectividad.columns for col in cols_necesarias):
         print(f"Error: Faltan columnas clave. Se necesitan: {cols_necesarias}")
         return None

    # Ordenar y resetear el índice para que las anotaciones funcionen
    df_chart = df_efectividad.sort_values(by='Efectividad', ascending=True).reset_index(drop=True)

    # --- 1. Formateo de Texto (como lo tenías) ---
    def format_text_efectividad(row):
        pct = f"{row['Efectividad']:.2%}".replace('.', ',')
        count = f"{row['Total_Conversaciones']:,.0f}".replace(',', '.')
        return f"<b>{pct}</b> ({count})"
        
    df_chart['Texto_Efectividad'] = df_chart.apply(format_text_efectividad, axis=1)

    def format_text_total(row):
        total = f"{row['Total_Entregados']:,.0f}".replace(',', '.')
        return f"<b>{total}</b>"
        
    df_chart['Texto_Total'] = df_chart.apply(format_text_total, axis=1)

    # --- 2. [NUEVO] Lógica de posicionamiento y color ---
    # Define un umbral. Si es >85%, el texto va adentro.
    umbral_colision = 0.85 
    
    df_chart['text_position'] = df_chart['Efectividad'].apply(
        lambda x: 'inside' if x > umbral_colision else 'outside'
    )
    df_chart['text_color'] = df_chart['Efectividad'].apply(
        lambda x: 'white' if x > umbral_colision else '#333333'
    )

    # --- 3. [NUEVO] Estilos de barra ---
    bar_thickness = 0.5
    border_radius_px = 15

    # --- 4. Crear la figura base ---
    fig = go.Figure()

    # --- 5. Barra de fondo (gris) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=[1] * len(df_chart), # Barra al 100%
        orientation='h',
        width=bar_thickness, # <-- Estilo
        marker=dict(
            color='rgba(230, 230, 230, 0.9)', 
            cornerradius=border_radius_px # <-- Estilo
        ), 
        hoverinfo='none',
        showlegend=False
        # [CAMBIO]: Quitamos el texto de aquí. Usaremos anotaciones.
    ))

    # --- 6. Barra de efectividad (azul) ---
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=df_chart['Efectividad'],
        orientation='h',
        width=bar_thickness, # <-- Estilo
        marker=dict(
            color='#3366CC',
            cornerradius=border_radius_px # <-- Estilo
        ), 
        hoverinfo='none',
        showlegend=False,
        text=df_chart['Texto_Efectividad'],
        
        # --- [CAMBIO CLAVE] ---
        # Usa las listas que creamos en Pandas
        textposition=df_chart['text_position'], 
        textfont=dict(
            color=df_chart['text_color'], 
            size=11,
            family="Arial, sans-serif"
        ),
        # Asegura que el texto "inside" se alinee a la derecha
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
            range=[0, 1.4], # Rango amplio para que quepan ambos textos
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(size=12, color='#333333'),
            # [CAMBIO]: Asegurar el orden de las categorías
            categoryorder='array',
            categoryarray=df_chart['Call_Center']
        ),
        yaxis_title=None,
        # [CAMBIO]: Aumentar margen derecho para el texto del total
        margin=dict(l=50, r=80, t=50, b=20), 
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400 # Ajusta la altura si es necesario
    )
    
    # --- 8. [NUEVO] Añadir el texto del 'Total_Entregados' usando anotaciones ---
    # Esto da un control preciso y evita TODAS las colisiones.
    for i, row in df_chart.iterrows():
        fig.add_annotation(
            x=1.03, # Posición X fija (un poco más allá del 100%)
            y=row['Call_Center'], # Posición Y basada en la categoría
            text=row['Texto_Total'],
            showarrow=False,
            font=dict(size=11, color='#333333', family="Arial, sans-serif"),
            xanchor='left', # Anclar el texto a la izquierda de la posición X
            yanchor='middle'
        )
    
    return fig