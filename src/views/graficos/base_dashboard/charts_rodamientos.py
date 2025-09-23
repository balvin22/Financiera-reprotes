import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from config import ORDEN_FRANJAS

COLOR_TEXTO = '#EAEAEA'

# --- FUNCIONES DE PREPARACIÓN DE DATOS (CACHEADAS) ---

@st.cache_data
def prepare_donut_data(df):
    """Calcula y cachea los datos para el gráfico de dona."""
    if df.empty or 'Total_Recaudo' not in df.columns:
        return None
    df['Estado_Pago'] = np.where(df['Total_Recaudo'] > 50000, 'PAGO', 'SIN PAGO')
    return df['Estado_Pago'].value_counts()

@st.cache_data
def prepare_sunburst_data(df_cartera, df_novedades):
    """Calcula y cachea los datos para los gráficos de sol (sunburst)."""
    if df_cartera.empty:
        return None, None
    
    df_cartera['Estado_Gestion'] = np.where(df_cartera['Cantidad_Novedades'] > 0, 'CON GESTIÓN', 'SIN GESTIÓN')
    
    # Esta es la operación más costosa que vamos a cachear
    cargos_por_cliente = df_novedades.drop_duplicates(subset=['Cedula_Cliente'])[['Cedula_Cliente', 'Cargo_Usuario']]
    df_merged = pd.merge(df_cartera, cargos_por_cliente, on='Cedula_Cliente', how='left')
    df_merged['Cargo_Usuario'] = df_merged['Cargo_Usuario'].fillna('')
    
    grouped = df_merged.groupby(['Estado_Gestion', 'Cargo_Usuario']).size().reset_index(name='Cantidad')
    grouped = grouped[~((grouped['Estado_Gestion'] == 'CON GESTIÓN') & (grouped['Cargo_Usuario'] == ''))]

    if grouped['Cantidad'].sum() == 0:
        return None, None
        
    return grouped, df_merged['Estado_Gestion'].value_counts()


# --- FUNCIONES DE GRÁFICOS (Ahora más rápidas) ---

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

def create_rodamiento_bar_chart(df):
    """
    Crea un gráfico de barras APILADAS mostrando el número de cuentas
    por Rodamiento, desglosado por Franja de Cartera.
    """
    # 1. Verificamos que existan las columnas necesarias
    if df.empty or 'Rodamiento' not in df.columns or 'Franja_Cartera' not in df.columns:
        return None

    # 2. Agrupamos y contamos por ambas categorías para obtener los datos de cada segmento
    chart_data = df.groupby(['Rodamiento', 'Franja_Cartera']).size().reset_index(name='Número de Cuentas')
    
    # 3. Ordenamos las franjas lógicamente para el gráfico y la leyenda
    # Usamos las franjas que realmente existen en los datos filtrados
    franjas_existentes = [f for f in ORDEN_FRANJAS if f in chart_data['Franja_Cartera'].unique()]
    chart_data['Franja_Cartera'] = pd.Categorical(chart_data['Franja_Cartera'], categories=franjas_existentes, ordered=True)
    
    # 4. Creamos la figura con Plotly Express
    fig = px.bar(
        chart_data,
        x='Rodamiento',
        y='Número de Cuentas',
        color='Franja_Cartera', # <-- Esta es la clave para apilar las barras
        title="<b>Cuentas por Rodamiento y Franja</b>",
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Vivid # Una paleta de colores con buen contraste
    )

    # 5. Ajustamos el diseño final
    fig.update_layout(
        barmode='stack', # Asegura que las barras estén apiladas una sobre otra
        title_font_color='#EAEAEA',
        xaxis_title="Estado de Rodamiento",
        yaxis_title="Número de Cuentas",
        font_color='#EAEAEA',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_title_text='Franja', # Añadimos un título a la leyenda
        showlegend=True # Activamos la leyenda
    )
    
    # Ajustamos el texto dentro de las barras para que sea más legible
    fig.update_traces(
        textfont_size=12,
        textangle=0,
        textposition='inside',
        insidetextanchor='middle' # Centra el texto en cada segmento
    )
    
    return fig