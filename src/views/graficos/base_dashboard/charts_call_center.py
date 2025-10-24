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
    llamadas por Call Center.
    
    [CAMBIO]: Muestra DOS etiquetas de texto:
    1. La efectividad (% y Con_Respuesta) al final de la barra azul.
    2. El Total_Intentos al final de la barra gris (100%).
    """
    if df_efectividad.empty:
        return None
    
    # Asegurarse de que las columnas necesarias existen
    if not all(col in df_efectividad.columns for col in ['Call_Center', 'Efectividad', 'Con_Respuesta', 'Total_Intentos']):
         print("Error: Faltan columnas clave en df_efectividad (Call_Center, Efectividad, Con_Respuesta, Total_Intentos)")
         return None

    df_chart = df_efectividad.sort_values(by='Efectividad', ascending=True)

    # 1. [NUEVO] Crear AMBOS formatos de texto
    
    # Texto para la barra azul (Efectividad)
    def format_text_efectividad(row):
        pct = f"{row['Efectividad']:.2%}".replace('.', ',')
        count = f"{row['Con_Respuesta']:,.0f}".replace(',', '.')
        return f"<b>{pct}</b> ({count})"
        
    df_chart['Texto_Efectividad'] = df_chart.apply(format_text_efectividad, axis=1)

    # Texto para la barra gris (Total)
    def format_text_total(row):
        total = f"{row['Total_Intentos']:,.0f}".replace(',', '.')
        return f"<b>{total}</b>"
        
    df_chart['Texto_Total'] = df_chart.apply(format_text_total, axis=1)


    # 2. Crear la figura base
    fig = go.Figure()

    # 3. [MODIFICADO] Añadir la barra de fondo (gris) con el texto del TOTAL
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=[1] * len(df_chart), # Barra al 100%
        orientation='h',
        marker=dict(color='rgba(230, 230, 230, 0.9)'), # Gris claro
        hoverinfo='none',
        showlegend=False,
        text=df_chart['Texto_Total'], # <-- [CAMBIO] Texto del Total
        textposition='outside',
        textfont=dict(color='#333333', size=11)
    ))

    # 4. [MODIFICADO] Añadir la barra de efectividad (azul) con el texto de EFECTIVIDAD
    fig.add_trace(go.Bar(
        y=df_chart['Call_Center'],
        x=df_chart['Efectividad'],
        orientation='h',
        marker=dict(color='#3366CC'), 
        hoverinfo='none',
        showlegend=False,
        text=df_chart['Texto_Efectividad'], # <-- [CAMBIO] Texto de Efectividad
        textposition='outside',
        textfont=dict(color='#333333', size=11) # Color del texto después de la barra azul
    ))

    # 5. Configurar el layout
    fig.update_layout(
        title_text='% = Llamadas con respuesta / Total de intentos',
        title_x=0.05, 
        title_font_size=14,
        title_font_family="Arial, sans-serif",
        barmode='overlay', 
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0, 1.4], # <-- Rango amplio para que quepan ambos textos
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(size=12, color='#333333')
        ),
        yaxis_title=None,
        margin=dict(l=50, r=20, t=50, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig