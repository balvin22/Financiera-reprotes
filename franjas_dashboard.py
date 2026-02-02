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

st.title("📊 Dashboard de Franjas y Rodamientos")
st.markdown("---")


# --- FUNCIÓN REUTILIZABLE PARA CREAR GRÁFICOS (FRANJAS) ---
def create_analysis_chart(df_data, group_value):
    """
    Crea un gráfico combinado a partir de datos ya filtrados para Franjas.
    """
    df_plot = df_data.groupby('MES', as_index=False, observed=True).agg({
        'META GNRL': 'sum',
        'RECAUDO $': 'sum',
        'ANTICIPO': 'sum',
        'Meta_Proyectada': 'sum',
        'CUMPLIMIENTO': 'mean',
        'RECAUDO %': 'mean'
    })

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df_plot['MES'], y=df_plot['META GNRL'], name='Meta General',
        marker_color='#ff7f0e', text=df_plot['META GNRL'].apply(lambda x: f"${x:,.0f}"), textposition='auto',
        textfont=dict(size=15)
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df_plot['MES'], y=df_plot['RECAUDO $'], name='Recaudo $',
        marker_color="#19679f", text=df_plot['RECAUDO $'].apply(lambda x: f"${x:,.0f}"), textposition='auto',
        textfont=dict(size=15)
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df_plot['MES'], y=df_plot['ANTICIPO'], name='Anticipo',
        marker_color="#b0d51d", text=df_plot['ANTICIPO'].apply(lambda x: f"${x:,.0f}"), textposition='auto',
        textfont=dict(size=15)
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df_plot['MES'], y=df_plot['Meta_Proyectada'], name='Meta Proyectada',
        marker_color='#e377c2', text=df_plot['Meta_Proyectada'].apply(lambda x: f"${x:,.0f}"), textposition='auto',
        textfont=dict(size=15)
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_plot['MES'], y=df_plot['CUMPLIMIENTO'], name='Cumplimiento %',
        mode='lines+markers+text', marker_color='#d62728',
        text=df_plot['CUMPLIMIENTO'].apply(lambda x: f"{x:.1%}"), textposition="top center", textfont=dict(color="#000000",size=15)
        ), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=df_plot['MES'], y=df_plot['RECAUDO %'], name='Recaudo %',
        mode='lines+markers+text', marker_color='#2ca02c',
        text=df_plot['RECAUDO %'].apply(lambda x: f"{x:.1%}"), textposition="bottom center", textfont=dict(color="#000000",size=15)
    ), secondary_y=True)

    fig.update_layout(
        barmode='group', title_text=f"Análisis de Franjas para: {group_value}", xaxis_title="Mes",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text="<b>Monto ($)</b>", secondary_y=False, tickformat="$,.0f")
    fig.update_yaxes(title_text="<b>Porcentaje (%)</b>", secondary_y=True, tickformat=".0%")
    return fig

# --- FUNCIÓN MODIFICADA PARA GRÁFICOS DE RODAMIENTOS (APILADO POR CANTIDAD) ---
def create_rodamientos_chart(df_data, group_value):
    """
    Crea un gráfico de barras apiladas con lógica inteligente para que
    los textos pequeños se vean en una sola línea y quepan en la barra.
    """
    # Agrupamos los datos
    df_plot = df_data.groupby('MES', as_index=False, observed=True).agg({
        'EMPEORO': 'sum',
        'MANTIENE': 'sum',
        'MEJORO': 'sum',
        'PAGO TOTAL': 'sum',
        'NORMALIZA':'sum'
    })

    # Calculamos el total
    df_plot['TOTAL_CUENTAS'] = (
        df_plot['EMPEORO'] + 
        df_plot['MANTIENE'] + 
        df_plot['MEJORO'] + 
        df_plot['PAGO TOTAL'] + 
        df_plot['NORMALIZA']
    )

    names = {
        'EMPEORO': 'Empeoró',
        'PAGO TOTAL': 'Pago Total',
        'MANTIENE': 'Mantiene',
        'MEJORO': 'Mejoró',
        'NORMALIZA':'Normaliza'
    }
    colors = {
        'Empeoró': '#d62728',     # Rojo
        'Pago Total': '#1f77b4',  # Azul
        'Mantiene': '#ff7f0e',    # Naranja
        'Mejoró': '#2ca02c',      # Verde
        'Normaliza': '#9467bd'    # Morado
    }

    fig = go.Figure()

    for col in names.keys():
        text_labels = []
        for val, total in zip(df_plot[col], df_plot['TOTAL_CUENTAS']):
            if val > 0 and total > 0:
                pct = (val / total) * 100
                
                # --- LÓGICA INTELIGENTE DE TEXTO ---
                # Si el porcentaje es menor al 12%, usamos UNA sola línea para ahorrar espacio vertical.
                # Si es mayor, usamos DOS líneas para mejor estética.
                if pct < 12:
                    # Formato compacto: "25 (10.5%)"
                    text_labels.append(f"<b>{val:,.0f}</b> ({pct:.1f}%)")
                else:
                    # Formato detallado con salto de línea:
                    # "25
                    # (10.5%)"
                    text_labels.append(f"<b>{val:,.0f}</b><br>({pct:.1f}%)")
            else:
                text_labels.append("")

        fig.add_trace(go.Bar(
            x=df_plot['MES'],
            y=df_plot[col],
            name=names[col],
            text=text_labels,
            textposition='inside', # Forzamos que esté adentro
            insidetextanchor='middle', # Centrado verticalmente
            marker_color=colors[names[col]],
            insidetextfont=dict(
                color='white', 
                size=12 # Tamaño base legible
            )
        ))

    # Totales arriba de la barra
    fig.add_trace(go.Scatter(
        x=df_plot['MES'],
        y=df_plot['TOTAL_CUENTAS'],
        text=df_plot['TOTAL_CUENTAS'].apply(lambda x: f"<b>{x:,.0f}</b>"),
        mode='text',
        textposition='top center',
        textfont=dict(size=16, color='black'), # Un poco más grande el total
        showlegend=False,
        hoverinfo='skip'
    ))

    max_y = df_plot['TOTAL_CUENTAS'].max()
    
    fig.update_layout(
        barmode='stack',
        title_text=f"Análisis de Rodamientos por Cantidad de Cuentas para: {group_value}",
        xaxis_title="Mes",
        yaxis_title="<b>Cantidad de Cuentas</b>",
        yaxis=dict(
            range=[0, max_y * 1.20] # 20% extra de aire arriba
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        
        # --- ESTO AYUDA A QUE SE VEAN LOS TEXTOS ---
        uniformtext_minsize=10, # Intenta no bajar de 10px
        uniformtext_mode='hide', # Si es IMPOSIBLE que quepa, lo oculta (para no manchar), pero con el formato de 1 línea debería caber casi todo.
        height=600 # <--- AUMENTAMOS ALTURA: Hacemos el gráfico más alto para que las barras tengan más píxeles verticales
    )
    return fig

# --- CARGADOR DE ARCHIVOS ---
st.sidebar.header("1. Cargar Archivo")
uploaded_file = st.sidebar.file_uploader("Selecciona un archivo Excel", type=['xlsx'])

if uploaded_file is not None:
    try:
        df_franjas = pd.read_excel(uploaded_file, sheet_name='FRANJAS')
        df_rodamientos = pd.read_excel(uploaded_file, sheet_name='RODAMIENTOS')
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # --- LIMPIEZA Y PREPARACIÓN DE DATOS (FRANJAS) ---
    cols_to_numeric_franjas = ['META GNRL', 'RECAUDO $', 'CUMPLIMIENTO', 'RECAUDO %']
    for col in cols_to_numeric_franjas:
        df_franjas[col] = pd.to_numeric(df_franjas[col], errors='coerce')
    df_franjas.dropna(subset=cols_to_numeric_franjas, inplace=True)
    cumplimiento_safe = df_franjas['CUMPLIMIENTO'].replace(0, np.nan)
    df_franjas['Meta_Proyectada'] = df_franjas['RECAUDO $'] / cumplimiento_safe
    df_franjas.fillna({'Meta_Proyectada': 0}, inplace=True)
    meses_ordenados = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    df_franjas['MES'] = pd.Categorical(df_franjas['MES'], categories=meses_ordenados, ordered=True)
    df_franjas.sort_values('MES', inplace=True)

    # --- LIMPIEZA Y PREPARACIÓN DE DATOS (RODAMIENTOS) ---
    cols_to_numeric_rodamientos = ['EMPEORO', 'MANTIENE', 'MEJORO', 'NORMALIZA','PAGO TOTAL']
    for col in cols_to_numeric_rodamientos:
        df_rodamientos[col] = pd.to_numeric(df_rodamientos[col], errors='coerce')
    df_rodamientos.dropna(subset=cols_to_numeric_rodamientos, inplace=True)
    df_rodamientos['MES'] = pd.Categorical(df_rodamientos['MES'], categories=meses_ordenados, ordered=True)
    df_rodamientos.sort_values('MES', inplace=True)

    # --- SEPARAR DATOS: ZONAS vs GESTORES (PARA AMBOS DATAFRAMES) ---
    df_franjas['ZONA'] = df_franjas['ZONA'].astype(str)
    df_gestores_franjas = df_franjas[df_franjas['ZONA'].str.startswith('G.')].copy()
    df_zonas_franjas = df_franjas[~df_franjas['ZONA'].str.startswith('G.')].copy()
    df_rodamientos['ZONA'] = df_rodamientos['ZONA'].astype(str)
    df_franjas['FRANJA'] = df_franjas['FRANJA'].astype(str)
    df_rodamientos['FRANJA'] = df_rodamientos['FRANJA'].astype(str)
    df_gestores_rodamientos = df_rodamientos[df_rodamientos['ZONA'].str.startswith('G.')].copy()
    df_zonas_rodamientos = df_rodamientos[~df_rodamientos['ZONA'].str.startswith('G.')].copy()

    # --- BARRA LATERAL CON FILTROS ---
    st.sidebar.header("2. Filtros Generales")
    all_regionals = sorted(pd.concat([df_franjas["REGIONAL"], df_rodamientos["REGIONAL"]]).unique())
    selected_regional = st.sidebar.multiselect("Regionales:", options=all_regionals, default=all_regionals)
    all_franjas = ['Todas'] + sorted(pd.concat([df_franjas["FRANJA"], df_rodamientos["FRANJA"]]).unique())
    selected_franja = st.sidebar.selectbox("Franja:", all_franjas)

    # --- APLICAR FILTROS A TODOS LOS DATAFRAMES ---
    df_zonas_franjas_filtrado = df_zonas_franjas[df_zonas_franjas["REGIONAL"].isin(selected_regional)]
    df_gestores_franjas_filtrado = df_gestores_franjas[df_gestores_franjas["REGIONAL"].isin(selected_regional)]
    df_zonas_rodamientos_filtrado = df_zonas_rodamientos[df_zonas_rodamientos["REGIONAL"].isin(selected_regional)]
    df_gestores_rodamientos_filtrado = df_gestores_rodamientos[df_gestores_rodamientos["REGIONAL"].isin(selected_regional)]
    if selected_franja != 'Todas':
        df_zonas_franjas_filtrado = df_zonas_franjas_filtrado[df_zonas_franjas_filtrado['FRANJA'] == selected_franja]
        df_gestores_franjas_filtrado = df_gestores_franjas_filtrado[df_gestores_franjas_filtrado['FRANJA'] == selected_franja]
        df_zonas_rodamientos_filtrado = df_zonas_rodamientos_filtrado[df_zonas_rodamientos_filtrado['FRANJA'] == selected_franja]
        df_gestores_rodamientos_filtrado = df_gestores_rodamientos_filtrado[df_gestores_rodamientos_filtrado['FRANJA'] == selected_franja]

    # --- PESTAÑAS PARA ZONAS Y GESTORES ---
    tab1, tab2, tab3 = st.tabs(["📈 Zonas (Análisis Franjas)", "📊 Zonas (Análisis Rodamientos)", "👥 Análisis por Gestor"])

    with tab1:
        st.header("Visualización de Franjas por Zona")
        zonas_disponibles = sorted(df_zonas_franjas_filtrado["ZONA"].unique())
        selected_zonas = st.multiselect("Selecciona las Zonas:", options=zonas_disponibles, default=zonas_disponibles, key="zonas_franjas")
        if not selected_zonas or df_zonas_franjas_filtrado.empty:
            st.warning("No hay datos de Zonas de Franjas para mostrar con los filtros seleccionados.")
        else:
            for zona in selected_zonas:
                df_single_zona = df_zonas_franjas_filtrado[df_zonas_franjas_filtrado['ZONA'] == zona]
                fig = create_analysis_chart(df_single_zona, zona)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")

    with tab2:
        st.header("Visualización de Rodamientos por Zona")
        zonas_rodamientos_disponibles = sorted(df_zonas_rodamientos_filtrado["ZONA"].unique())
        selected_zonas_rodamientos = st.multiselect("Selecciona las Zonas:", options=zonas_rodamientos_disponibles, default=zonas_rodamientos_disponibles, key="zonas_rodamientos")
        if not selected_zonas_rodamientos or df_zonas_rodamientos_filtrado.empty:
            st.warning("No hay datos de Zonas de Rodamientos para mostrar con los filtros seleccionados.")
        else:
            for zona in selected_zonas_rodamientos:
                df_single_zona_rodamientos = df_zonas_rodamientos_filtrado[df_zonas_rodamientos_filtrado['ZONA'] == zona]
                fig = create_rodamientos_chart(df_single_zona_rodamientos, zona)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")

    with tab3:
        st.header("Visualización por Gestores (Análisis Combinado)")
        gestores_disponibles = sorted(df_gestores_franjas_filtrado["ZONA"].unique())
        selected_gestores = st.multiselect("Selecciona los Gestores:", options=gestores_disponibles, default=gestores_disponibles, key="gestores_franjas")
        if not selected_gestores or df_gestores_franjas_filtrado.empty:
            st.warning("No hay datos de Gestores para mostrar con los filtros seleccionados.")
        else:
            for gestor in selected_gestores:
                st.subheader(f"Análisis para Gestor: {gestor}")
                
                # --- Gráfico de Franjas ---
                df_single_gestor_franjas = df_gestores_franjas_filtrado[df_gestores_franjas_filtrado['ZONA'] == gestor]
                if not df_single_gestor_franjas.empty:
                    fig_franjas = create_analysis_chart(df_single_gestor_franjas, gestor)
                    st.plotly_chart(fig_franjas, use_container_width=True)
                
                # --- Gráfico de Rodamientos ---
                df_single_gestor_rodamientos = df_gestores_rodamientos_filtrado[df_gestores_rodamientos_filtrado['ZONA'] == gestor]
                if not df_single_gestor_rodamientos.empty:
                    fig_rodamientos = create_rodamientos_chart(df_single_gestor_rodamientos, gestor)
                    st.plotly_chart(fig_rodamientos, use_container_width=True)
                
                st.markdown("---")
else:
    st.info("👆 Por favor, carga tu archivo de datos para comenzar.")