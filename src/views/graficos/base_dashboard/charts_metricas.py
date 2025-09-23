# charts.py
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from config import ORDEN_FRANJAS, ZONA_COBRO_MAP

def create_regional_bar_chart(df):
    """Crea un gráfico de barras por Regional de Venta."""
    df_grafico = df.groupby(['Regional_Venta', 'Franja_Meta']).size().reset_index(name='count')
    df_grafico['Franja_Meta'] = pd.Categorical(df_grafico['Franja_Meta'], categories=ORDEN_FRANJAS, ordered=True)
    df_grafico = df_grafico.sort_values('Franja_Meta')

    fig = px.bar(
        df_grafico, x='Regional_Venta', y='count', color='Franja_Meta',
        title="<b>Total de Cuentas por Regional</b>",
        labels={'count': 'Cantidad de Cuentas', 'Regional_Venta': 'Regional', 'Franja_Meta': 'Franja'},
        template='plotly_white', text_auto=True
    )
    return fig

def create_cobro_bar_chart(df):
    """Crea un gráfico de barras por Grupo de Cobro."""
    if 'Regional_Cobro' not in df.columns or 'Zona_Cobro' not in df.columns:
        return None

    df_copy = df.copy()
    mapped_zonas = df_copy['Zona_Cobro'].map(ZONA_COBRO_MAP)
    df_copy['Regional_Cobro'] = df_copy['Regional_Cobro'].replace('nan', np.nan)
    df_copy['Eje_X_Cobro'] = df_copy['Regional_Cobro'].fillna(mapped_zonas)
    df_copy.dropna(subset=['Eje_X_Cobro'], inplace=True)

    df_grafico = df_copy.groupby(['Eje_X_Cobro', 'Franja_Meta']).size().reset_index(name='count')
    df_grafico['Franja_Meta'] = pd.Categorical(df_grafico['Franja_Meta'], categories=ORDEN_FRANJAS, ordered=True)
    df_grafico = df_grafico.sort_values('Franja_Meta')

    if df_grafico.empty:
        return None

    fig = px.bar(
        df_grafico, x='Eje_X_Cobro', y='count', color='Franja_Meta',
        title="<b>Total de Cuentas por Grupo de Cobro</b>",
        labels={'count': 'Cantidad de Cuentas', 'Eje_X_Cobro': 'Grupo de Cobro', 'Franja_Meta': 'Franja'},
        template='plotly_white', text_auto=True
    )
    return fig

def create_desembolso_por_ano_chart(df):
    """
    Crea un gráfico de barras del valor desembolsado por año,
    mostrando siempre desde 2018 hasta el año actual y ordenado por año.
    """
    df_copy = df.copy()

    df_copy['Fecha_Desembolso'] = pd.to_datetime(df_copy['Fecha_Desembolso'], errors='coerce')
    df_copy.dropna(subset=['Fecha_Desembolso'], inplace=True)
    df_copy['Año_Desembolso'] = df_copy['Fecha_Desembolso'].dt.year

    # --- Lógica de filtrado dinámico ---
    start_year = 2018
    end_year = datetime.now().year

    df_copy = df_copy[
        (df_copy['Año_Desembolso'] >= start_year) &
        (df_copy['Año_Desembolso'] <= end_year)
    ]
    
    if df_copy.empty:
        return None

    # Agrupar por año y franja, y sumar el valor del desembolso
    df_grafico = df_copy.groupby(['Año_Desembolso', 'Franja_Meta'])['Valor_Desembolso'].sum().reset_index()
    # --- LÍNEA CLAVE AÑADIDA ---
    # **Aseguramos que los datos estén ordenados por año antes de graficar**
    df_grafico.sort_values('Año_Desembolso', inplace=True)
    # Ordenar las franjas para que la leyenda del gráfico se vea consistente
    df_grafico['Franja_Meta'] = pd.Categorical(df_grafico['Franja_Meta'], categories=ORDEN_FRANJAS, ordered=True)

    # El resto de la función sigue igual...
    fig = px.bar(
        df_grafico,
        x='Año_Desembolso',
        y='Valor_Desembolso',
        color='Franja_Meta',
        title=f"<b>Valor Desembolsado ({start_year} - {end_year})</b>",
        labels={
            'Año_Desembolso': 'Año de Desembolso',
            'Valor_Desembolso': 'Suma del Valor Desembolsado ($)',
            'Franja_Meta': 'Franja de Mora'
        },
        template='plotly_white',
        text_auto='.2s'
    )

    fig.update_layout(xaxis={'type': 'category'})
    fig.update_traces(textposition='inside')

    return fig

def create_vigencia_sunburst_chart(df):
    """
    Crea un gráfico de sol (sunburst) mostrando la distribución de cuotas.
    La categoría 'VIGENTES' se subdivide por día del mes para las cuotas del mes actual.
    """
    df_copy = df.copy()

    if 'Fecha_Cuota_Vigente' not in df_copy.columns:
        return None

    # 1. Clasificación inicial en las tres categorías principales
    df_copy['Estado_Vigencia_Agrupado'] = df_copy['Fecha_Cuota_Vigente'].astype(str)
    df_copy.loc[~df_copy['Estado_Vigencia_Agrupado'].isin(['ANTICIPADO', 'VIGENCIA EXPIRADA']), 'Estado_Vigencia_Agrupado'] = 'VIGENTES'

    # 2. Preparamos la columna para las subdivisiones, inicializándola vacía
    df_copy['Sub_Estado_Vigencia'] = ''

    # Máscara para identificar todos los créditos que son 'VIGENTES'
    vigentes_mask = df_copy['Estado_Vigencia_Agrupado'] == 'VIGENTES'

    if vigentes_mask.any():
        # Obtenemos el índice de las filas que son 'VIGENTES'
        vigentes_indices = df_copy[vigentes_mask].index
        
        # Convertimos solo las fechas de las filas 'VIGENTES' a datetime
        fechas_reales = pd.to_datetime(df_copy.loc[vigentes_indices, 'Fecha_Cuota_Vigente'], errors='coerce')

        # Obtenemos el mes y año actual para el filtro
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Filtramos las fechas para quedarnos solo con las del mes actual
        fechas_mes_actual = fechas_reales[(fechas_reales.dt.year == current_year) & (fechas_reales.dt.month == current_month)]

        # Si encontramos fechas en el mes actual, creamos las etiquetas
        if not fechas_mes_actual.empty:
            # Creamos las etiquetas "Día X"
            subdivision_labels = fechas_mes_actual.dt.day.apply(lambda d: f"Día {d}")
            
            # Asignamos las etiquetas de vuelta a la columna 'Sub_Estado_Vigencia' en df_copy,
            # usando el índice de las fechas filtradas para garantizar la asignación correcta.
            df_copy.loc[fechas_mes_actual.index, 'Sub_Estado_Vigencia'] = subdivision_labels

    # Agrupamos los datos para el gráfico.
    df_sunburst = df_copy.groupby(['Estado_Vigencia_Agrupado', 'Sub_Estado_Vigencia']).size().reset_index(name='count')

    if df_sunburst.empty:
        return None

    # (El resto de la función para crear la figura es igual)
    fig = px.sunburst(
        df_sunburst,
        path=['Estado_Vigencia_Agrupado', 'Sub_Estado_Vigencia'],
        values='count',
        title="<b>Distribución de Cuotas por Estado de Vigencia</b>",
        color='Estado_Vigencia_Agrupado',
        template='plotly_white'
    )

    fig.update_traces(
        textinfo='label+percent parent',
        insidetextorientation='radial',
        sort=True
    )
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))

    return fig