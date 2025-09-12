import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Recaudo",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Franjas de Recaudo")
st.markdown("---")


# --- FUNCIÓN REUTILIZABLE PARA CREAR GRÁFICOS (AHORA MÁS SIMPLE) ---
def create_analysis_chart(df_data, group_value):
    """
    Crea un gráfico combinado a partir de datos ya filtrados.
    """
    # Agrupar los datos por mes para la visualización
    df_plot = df_data.groupby('MES', as_index=False, observed=True).agg({
        'META GNRL': 'sum',
        'RECAUDO $': 'sum',
        'Meta_Proyectada': 'sum',
        'CUMPLIMIENTO': 'mean',
        'RECAUDO %': 'mean'
    })

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # BARRA de Meta General
    fig.add_trace(go.Bar(
        x=df_plot['MES'], y=df_plot['META GNRL'], name='Meta General',
        marker_color='#ff7f0e', text=df_plot['META GNRL'].apply(lambda x: f"${x:,.0f}"), textposition='auto',
        textfont=dict(size=15)
    ), secondary_y=False)

    # BARRA de Recaudo
    fig.add_trace(go.Bar(
        x=df_plot['MES'], y=df_plot['RECAUDO $'], name='Recaudo $',
        marker_color='#1f77b4', text=df_plot['RECAUDO $'].apply(lambda x: f"${x:,.0f}"), textposition='auto',
        textfont=dict(size=15)
    ), secondary_y=False)

    # --- NUEVA BARRA de Meta Proyectada ---
    fig.add_trace(go.Bar(
        x=df_plot['MES'], y=df_plot['Meta_Proyectada'], name='Meta Proyectada',
        marker_color='#e377c2', text=df_plot['Meta_Proyectada'].apply(lambda x: f"${x:,.0f}"), textposition='auto',
        textfont=dict(size=15)
    ), secondary_y=False)

    # LÍNEA de Cumplimiento
    fig.add_trace(go.Scatter(
        x=df_plot['MES'], y=df_plot['CUMPLIMIENTO'], name='Cumplimiento %',
        mode='lines+markers+text', marker_color='#d62728',
        text=df_plot['CUMPLIMIENTO'].apply(lambda x: f"{x:.1%}"), textposition="top center", textfont=dict(color="#000000",size=15)
        ), secondary_y=True)

    # LÍNEA de Recaudo %
    fig.add_trace(go.Scatter(
        x=df_plot['MES'], y=df_plot['RECAUDO %'], name='Recaudo %',
        mode='lines+markers+text', marker_color='#2ca02c',
        text=df_plot['RECAUDO %'].apply(lambda x: f"{x:.1%}"), textposition="bottom center", textfont=dict(color="#000000",size=15)
    ), secondary_y=True)

    # Actualizar el layout del gráfico
    fig.update_layout(
        barmode='group', title_text=f"Análisis para: {group_value}", xaxis_title="Mes",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_yaxes(title_text="<b>Monto ($)</b>", secondary_y=False, tickformat="$,.0f")
    fig.update_yaxes(title_text="<b>Porcentaje (%)</b>", secondary_y=True, tickformat=".0%")

    return fig

# --- CARGADOR DE ARCHIVOS ---
st.sidebar.header("1. Cargar Archivo")
uploaded_file = st.sidebar.file_uploader("Selecciona un archivo CSV o Excel", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # --- LIMPIEZA Y PREPARACIÓN DE DATOS ---
    cols_to_numeric = ['META GNRL', 'RECAUDO $', 'CUMPLIMIENTO', 'RECAUDO %']
    for col in cols_to_numeric:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=cols_to_numeric, inplace=True)

    # --- NUEVO CÁLCULO: Meta_Proyectada ---
    # Para evitar división por cero, reemplazamos 0 en CUMPLIMIENTO con NaN temporalmente
    cumplimiento_safe = df['CUMPLIMIENTO'].replace(0, np.nan)
    df['Meta_Proyectada'] = df['RECAUDO $'] / cumplimiento_safe
    df.fillna({'Meta_Proyectada': 0}, inplace=True) # Reemplazar resultados nulos (de la división por cero) con 0

    meses_ordenados = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    df['MES'] = pd.Categorical(df['MES'], categories=meses_ordenados, ordered=True)
    df.sort_values('MES', inplace=True)

    # --- SEPARAR DATOS: ZONAS vs GESTORES ---
    df['ZONA'] = df['ZONA'].astype(str)
    df_gestores = df[df['ZONA'].str.startswith('G.')].copy()
    df_zonas = df[~df['ZONA'].str.startswith('G.')].copy()

    # --- BARRA LATERAL CON FILTROS ---
    st.sidebar.header("2. Filtros Generales")
    selected_regional = st.sidebar.multiselect(
        "Regionales:",
        options=sorted(df["REGIONAL"].unique()),
        default=df["REGIONAL"].unique()
    )

    # --- NUEVO FILTRO GLOBAL DE FRANJAS ---
    franjas_disponibles = ['Todas'] + sorted(df["FRANJA"].unique())
    selected_franja = st.sidebar.selectbox("Franja:", franjas_disponibles)

    # Aplicar filtro de regional
    df_zonas_filtrado = df_zonas[df_zonas["REGIONAL"].isin(selected_regional)]
    df_gestores_filtrado = df_gestores[df_gestores["REGIONAL"].isin(selected_regional)]

    # Aplicar filtro de franja (si no es 'Todas')
    if selected_franja != 'Todas':
        df_zonas_filtrado = df_zonas_filtrado[df_zonas_filtrado['FRANJA'] == selected_franja]
        df_gestores_filtrado = df_gestores_filtrado[df_gestores_filtrado['FRANJA'] == selected_franja]

    # --- PESTAÑAS PARA ZONAS Y GESTORES ---
    tab1, tab2 = st.tabs(["📈 Análisis por Zona", "👥 Análisis por Gestor"])

    with tab1:
        st.header("Visualización por Zonas")
        zonas_disponibles = sorted(df_zonas_filtrado["ZONA"].unique())
        selected_zonas = st.multiselect("Selecciona las Zonas:", options=zonas_disponibles, default=zonas_disponibles)

        if not selected_zonas or df_zonas_filtrado.empty:
            st.warning("No hay datos de Zonas para mostrar con los filtros seleccionados.")
        else:
            for zona in selected_zonas:
                df_single_zona = df_zonas_filtrado[df_zonas_filtrado['ZONA'] == zona]
                fig = create_analysis_chart(df_single_zona, zona)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")

    with tab2:
        st.header("Visualización por Gestores")
        gestores_disponibles = sorted(df_gestores_filtrado["ZONA"].unique())
        selected_gestores = st.multiselect("Selecciona los Gestores:", options=gestores_disponibles, default=gestores_disponibles)

        if not selected_gestores or df_gestores_filtrado.empty:
            st.warning("No hay datos de Gestores para mostrar con los filtros seleccionados.")
        else:
            for gestor in selected_gestores:
                df_single_gestor = df_gestores_filtrado[df_gestores_filtrado['ZONA'] == gestor]
                fig = create_analysis_chart(df_single_gestor, gestor)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")

else:
    st.info("👆 Por favor, carga tu archivo de datos para comenzar.")