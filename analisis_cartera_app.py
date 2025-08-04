# analisis_cartera_app.py (Versión 4.1)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Gerencial de Cartera",
    layout="wide"
)

# --- CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def load_and_clean_data(file_path, sheet_name):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}.")
        return None

    # --- LIMPIEZA Y TRANSFORMACIÓN ---
    df['Fecha_Desembolso'] = pd.to_datetime(df['Fecha_Desembolso'], errors='coerce')
    
    numeric_cols = [
        'Valor_Desembolso', 'Saldo_Capital', 'Dias_Atraso', 'Cuotas_Pagadas', 'Total_Cuotas', 
        'Saldo_Interes_Corriente', 'Saldo_Avales', 'Meta_General', 'Valor_Cuota_Atraso'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Limpieza de la columna Meta_% que puede venir como texto con '%'
    if 'Meta_%' in df.columns:
        df['Meta_%'] = pd.to_numeric(df['Meta_%'].astype(str).str.replace('%', '', regex=False), errors='coerce')

    essential_cols = ['Fecha_Desembolso', 'Valor_Desembolso', 'Saldo_Capital', 'Total_Cuotas', 'Cuotas_Pagadas', 'Nombre_Cliente']
    df.dropna(subset=essential_cols, inplace=True)

    # Añadimos las nuevas columnas categóricas para los filtros
    categorical_cols = [
        'Nombre_Ciudad', 'Regional_Venta', 'Nombre_Vendedor', 'Franja_Mora', 'Empresa', 
        'Jefe_ventas', 'Cobrador', 'Vendedor_Activo', 'Zona', 'Nombre_Producto',
        'Regional_Cobro', 'Gestor', 'Codeudor1', 'Codeudor2'
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna('NO ESPECIFICADO').astype(str).str.strip().str.upper()
    
    df['Nombre_Cliente'] = df['Nombre_Cliente'].astype(str)

    # --- CREACIÓN DE MÉTRICAS AVANZADAS ---
    df['Año_Desembolso'] = df['Fecha_Desembolso'].dt.year
    df['Mes_Desembolso'] = df['Fecha_Desembolso'].dt.to_period('M').astype(str)
    
    df = df[df['Total_Cuotas'] > 0].copy()
    df['% Avance'] = (df['Cuotas_Pagadas'] / df['Total_Cuotas']) * 100
    df['% Avance'] = df['% Avance'].clip(0, 100)
    df['Cartera_Vencida'] = df.apply(lambda row: row['Saldo_Capital'] if row['Dias_Atraso'] > 0 else 0, axis=1)
    
    return df

# --- Carga de datos ---
df = load_and_clean_data('Reporte_Consolidado_Final_Prueba.xlsx', 'Reporte Consolidado')

# --- INICIO DE LA APP ---
if df is not None:
    st.title("🏆 Dashboard Gerencial de Cartera ")
    st.markdown(f"Análisis integral para la toma de decisiones. Lunes, 4 de Agosto de 2025 | Popayán, Cauca")

    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("Filtros Globales")
    
    st.sidebar.subheader("Filtros por Jerarquía y Estado")
    jefe_seleccionado = st.sidebar.multiselect("Jefe de Ventas", sorted(df['Jefe_ventas'].unique()), default=sorted(df['Jefe_ventas'].unique()))
    cobrador_seleccionado = st.sidebar.multiselect("Cobrador", sorted(df['Cobrador'].unique()), default=sorted(df['Cobrador'].unique()))
    
    st.sidebar.subheader("Filtros por Categoría")
    empresa_seleccionada = st.sidebar.multiselect("Empresa", sorted(df['Empresa'].unique()), default=sorted(df['Empresa'].unique()))
    regional_seleccionada = st.sidebar.multiselect("Regional de Venta", sorted(df['Regional_Venta'].unique()), default=sorted(df['Regional_Venta'].unique()))
    franja_seleccionada = st.sidebar.multiselect("Franja de Mora", sorted(df['Franja_Mora'].unique()), default=sorted(df['Franja_Mora'].unique()))
    
    st.sidebar.subheader("Filtros por Rango y Búsqueda")
    año_seleccionado = st.sidebar.multiselect("Año de Desembolso", sorted(df['Año_Desembolso'].astype(int).unique(), reverse=True), default=sorted(df['Año_Desembolso'].astype(int).unique(), reverse=True))
    min_dias, max_dias = int(df['Dias_Atraso'].min()), int(df['Dias_Atraso'].max())
    rango_dias_atraso = st.sidebar.slider("Rango de Días de Atraso:", min_dias, max_dias, (min_dias, max_dias))
    cliente_buscado = st.sidebar.text_input("Buscar por Nombre de Cliente:")

    # --- SECCIÓN DE NUEVOS FILTROS INTEGRADA ---
    st.sidebar.subheader("Filtros Avanzados Adicionales")

    vendedores_activos = st.sidebar.multiselect("Vendedor Activo", options=sorted(df['Vendedor_Activo'].unique()), default=sorted(df['Vendedor_Activo'].unique()))
    zonas_disponibles = st.sidebar.multiselect("Zona", options=sorted(df['Zona'].unique()), default=sorted(df['Zona'].unique()))
    productos_disponibles = st.sidebar.multiselect("Nombre del Producto", options=sorted(df['Nombre_Producto'].unique()), default=sorted(df['Nombre_Producto'].unique()))
    regionales_cobro = st.sidebar.multiselect("Regional de Cobro", options=sorted(df['Regional_Cobro'].unique()), default=sorted(df['Regional_Cobro'].unique()))
    gestores_disponibles = st.sidebar.multiselect("Gestor", options=sorted(df['Gestor'].unique()), default=sorted(df['Gestor'].unique()))

    rango_meta_pct = None
    if 'Meta_%' in df.columns and pd.api.types.is_numeric_dtype(df['Meta_%']):
        df_meta_pct_clean = df['Meta_%'].dropna()
        min_meta, max_meta = int(df_meta_pct_clean.min()), int(df_meta_pct_clean.max())
        rango_meta_pct = st.sidebar.slider("Rango de Meta %:", min_meta, max_meta, (min_meta, max_meta))

    rango_meta_tr_pct = None
    if 'Meta_T.R_%' in df.columns and pd.api.types.is_numeric_dtype(df['Meta_T.R_%']):
        df_meta_tr_clean = df['Meta_T.R_%'].dropna()
        min_meta_tr, max_meta_tr = int(df_meta_tr_clean.min()), int(df_meta_tr_clean.max())
        rango_meta_tr_pct = st.sidebar.slider("Rango de Meta T.R %:", min_meta_tr, max_meta_tr, (min_meta_tr, max_meta_tr))
    
    
    filtrar_con_codeudor = st.sidebar.checkbox("Mostrar solo créditos con Codeudores", value=False)
    
    # --- APLICACIÓN DE TODOS LOS FILTROS ---
    df_filtrado = df[
        (df['Jefe_ventas'].isin(jefe_seleccionado)) &
        (df['Cobrador'].isin(cobrador_seleccionado)) &
        (df['Empresa'].isin(empresa_seleccionada)) &
        (df['Regional_Venta'].isin(regional_seleccionada)) &
        (df['Franja_Mora'].isin(franja_seleccionada)) &
        (df['Año_Desembolso'].isin(año_seleccionado)) &
        (df['Dias_Atraso'].between(rango_dias_atraso[0], rango_dias_atraso[1])) &
        (df['Nombre_Cliente'].str.contains(cliente_buscado, case=False, na=False)) &
        (df['Vendedor_Activo'].isin(vendedores_activos)) &
        (df['Zona'].isin(zonas_disponibles)) &
        (df['Nombre_Producto'].isin(productos_disponibles)) &
        (df['Regional_Cobro'].isin(regionales_cobro)) &
        (df['Gestor'].isin(gestores_disponibles))
    ]
    
    if rango_meta_pct is not None:
        df_filtrado = df_filtrado[df_filtrado['Meta_%'].between(rango_meta_pct[0], rango_meta_pct[1])]
    if rango_meta_tr_pct is not None:
        df_filtrado = df_filtrado[df_filtrado['Meta_T.R_%'].between(rango_meta_tr_pct[0], rango_meta_tr_pct[1])]


    # --- ESTRUCTURA DE PESTAÑAS (El contenido de las pestañas no cambia) ---
    tab_list = ["📊 Resumen Gerencial", "🎯 Desempeño vs. Metas", "🔥 Análisis de Riesgo y Mora", "👥 Desempeño y Geografía", "📋 Explorador de Datos"]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_list)

    # (El código para cada pestaña se mantiene igual, ya que solo hemos cambiado los filtros)
    with tab1:
            st.header("Visión General de la Cartera")
            st.info("Indicadores de alto nivel sobre la salud y composición de la cartera, mostrando una foto general del estado actual del negocio.")
            
            # --- CÁLCULO DE TODOS LOS KPIs ---
            # Fila 1: KPIs de Montos y Riesgo
            saldo_capital = df_filtrado['Saldo_Capital'].sum()
            valor_desembolsado = df_filtrado['Valor_Desembolso'].sum()
            cartera_vencida = df_filtrado['Cartera_Vencida'].sum()
            saldo_interes = df_filtrado['Saldo_Interes_Corriente'].sum()
            
            # Fila 2: KPIs de Operación y Eficiencia
            num_creditos = df_filtrado['Credito'].nunique()
            promedio_dias_mora = df_filtrado['Dias_Atraso'].mean() if not df_filtrado.empty else 0
            ticket_promedio = df_filtrado['Valor_Desembolso'].mean() if not df_filtrado.empty else 0
            porc_cartera_vencida = (cartera_vencida / saldo_capital * 100) if saldo_capital > 0 else 0


            # --- MOSTRAR KPIs EN DOS FILAS ---
            st.markdown("##### Métricas Financieras Principales")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Saldo de Capital", f"${saldo_capital:,.0f}")
            col2.metric("Total Desembolsado", f"${valor_desembolsado:,.0f}")
            col3.metric("Cartera Vencida (Capital)", f"${cartera_vencida:,.0f}", f"{porc_cartera_vencida:.2f}% del total")
            col4.metric("Saldo Intereses Corrientes", f"${saldo_interes:,.0f}")

            st.markdown("##### Métricas Operativas")
            col5, col6, col7 = st.columns(3)
            col5.metric("Nº de Créditos Activos", f"{num_creditos:,}")
            col6.metric("Promedio Días de Atraso", f"{promedio_dias_mora:.1f} días")
            col7.metric("Ticket Promedio de Crédito", f"${ticket_promedio:,.0f}")
            
            st.markdown("---")
            
            # --- SECCIÓN DE GRÁFICOS MEJORADA ---
            col_line, col_hist = st.columns(2)
            with col_line:
                st.subheader("Evolución de Desembolsos")
                desembolsos_por_mes = df_filtrado.groupby('Mes_Desembolso')['Valor_Desembolso'].sum().reset_index()
                fig_lineas = px.line(desembolsos_por_mes, x='Mes_Desembolso', y='Valor_Desembolso', markers=True, title="Desembolsos Mensuales")
                st.plotly_chart(fig_lineas, use_container_width=True)
                
            with col_hist:
                st.subheader("Salud de la Cartera (% Avance)")
                fig_hist = px.histogram(df_filtrado, x='% Avance', nbins=20, title="Distribución del Avance de Créditos")
                fig_hist.update_layout(yaxis_title="Cantidad de Créditos")
                st.plotly_chart(fig_hist, use_container_width=True)

            st.markdown("---")
            
            # --- NUEVA FILA DE GRÁFICOS ---
            col_dona, col_tree = st.columns(2)
            with col_dona:
                st.subheader("Composición de Cartera por Empresa")
                if not df_filtrado.empty:
                    data_empresa = df_filtrado.groupby('Empresa')['Saldo_Capital'].sum().reset_index()
                    fig_dona = px.pie(
                        data_empresa,
                        names='Empresa',
                        values='Saldo_Capital',
                        title='Distribución del Saldo de Capital',
                        hole=0.4 # Esto lo convierte en un gráfico de dona
                    )
                    fig_dona.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_dona, use_container_width=True)
                else:
                    st.warning("No hay datos para mostrar.")

            with col_tree:
                st.subheader("Productos más Representativos por Desembolso")
                if not df_filtrado.empty:
                    # Excluimos productos no especificados para un gráfico más limpio
                    df_productos = df_filtrado[df_filtrado['Nombre_Producto'] != 'NO ESPECIFICADO']
                    data_tree = df_productos.groupby('Nombre_Producto')['Valor_Desembolso'].sum().nlargest(15).reset_index()
                    fig_tree = px.treemap(
                        data_tree,
                        path=[px.Constant("Todos los Productos"), 'Nombre_Producto'],
                        values='Valor_Desembolso',
                        title='Top 15 Productos por Valor Desembolsado'
                    )
                    fig_tree.update_traces(root_color="lightgrey")
                    fig_tree.update_layout(margin = dict(t=50, l=25, r=25, b=25))
                    st.plotly_chart(fig_tree, use_container_width=True)
                else:
                    st.warning("No hay datos para mostrar.")
    with tab2:
        st.header("Análisis de Cumplimiento de Metas")
        st.info("Mide el rendimiento frente a objetivos, analiza tendencias temporales y explora el desempeño detallado de cada equipo de ventas.")

        # --- Agregación de Datos para la Pestaña ---
        data_metas_jefes = df_filtrado.groupby('Jefe_ventas').agg(
            Saldo_Capital=('Saldo_Capital', 'sum'),
            Meta_General=('Meta_General', 'sum')
        ).reset_index()
        data_metas_jefes = data_metas_jefes[data_metas_jefes['Meta_General'] > 0]
        data_metas_jefes['% Cumplimiento'] = (data_metas_jefes['Saldo_Capital'] / data_metas_jefes['Meta_General'] * 100).fillna(0)

        # --- KPIs de Resumen de Metas ---
        saldo_total_filtrado = data_metas_jefes['Saldo_Capital'].sum()
        meta_total_filtrada = data_metas_jefes['Meta_General'].sum()
        cumplimiento_general = (saldo_total_filtrado / meta_total_filtrada * 100) if meta_total_filtrada > 0 else 0
        
        st.metric("Cumplimiento General de Meta (Filtrado)", f"{cumplimiento_general:.2f}%", f"Diferencia: ${saldo_total_filtrado - meta_total_filtrada:,.0f}")
        
        st.markdown("---")

        # --- Visualizaciones Principales ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Rendimiento por Jefe de Ventas")
            fig_bullet = go.Figure(go.Bar(
                y=data_metas_jefes['Jefe_ventas'],
                x=data_metas_jefes['% Cumplimiento'],
                orientation='h',
                text=data_metas_jefes['% Cumplimiento'].apply(lambda x: f"{x:.1f}%"),
                textposition='inside'
            ))
            fig_bullet.add_vline(x=100, line_width=3, line_dash="dash", line_color="red", annotation_text="Meta 100%")
            fig_bullet.update_layout(title_text="Porcentaje de Cumplimiento vs Meta", yaxis_title="Jefe de Ventas", xaxis_title="% Cumplimiento")
            st.plotly_chart(fig_bullet, use_container_width=True)
            
        with col2:
            st.subheader("Tendencia de Cumplimiento Mensual")
            data_tendencia = df_filtrado.groupby('Mes_Desembolso').agg(
                Saldo_Capital=('Saldo_Capital', 'sum'),
                Meta_General=('Meta_General', 'sum')
            ).reset_index()
            data_tendencia = data_tendencia[data_tendencia['Meta_General'] > 0]
            data_tendencia['% Cumplimiento'] = (data_tendencia['Saldo_Capital'] / data_tendencia['Meta_General'] * 100).fillna(0)
            
            fig_tendencia = px.line(data_tendencia, x='Mes_Desembolso', y='% Cumplimiento', markers=True, title="Evolución del % de Cumplimiento General")
            st.plotly_chart(fig_tendencia, use_container_width=True)

        st.markdown("---")
        
        # --- Análisis Detallado por Equipo (Drill-Down) ---
        st.subheader("Análisis Detallado por Equipo (Drill-Down)")
        jefe_seleccionado = st.selectbox("Selecciona un Jefe de Ventas para ver su equipo:", options=data_metas_jefes['Jefe_ventas'])
        
        if jefe_seleccionado:
            df_equipo = df_filtrado[df_filtrado['Jefe_ventas'] == jefe_seleccionado]
            data_vendedores = df_equipo.groupby('Nombre_Vendedor').agg(
                Saldo_Capital=('Saldo_Capital', 'sum'),
                Meta_General=('Meta_General', 'sum')
            ).reset_index()
            data_vendedores = data_vendedores[data_vendedores['Meta_General'] > 0]
            data_vendedores['% Cumplimiento'] = (data_vendedores['Saldo_Capital'] / data_vendedores['Meta_General'] * 100).fillna(0)

            fig_vendedores = px.bar(data_vendedores, x='Nombre_Vendedor', y='% Cumplimiento', text_auto='.2f', title=f"Desempeño de Vendedores del equipo de {jefe_seleccionado}")
            st.plotly_chart(fig_vendedores, use_container_width=True)

    with tab3:
        st.header("Análisis de Riesgo y Concentración de Mora")
        st.info("Aquí se identifica la calidad de la cartera por 'cosecha' (Vintage), se proyecta el riesgo futuro y se analiza la composición de la mora.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Análisis Vintage por Mes de Desembolso")
            
            df_vintage = df_filtrado.groupby('Mes_Desembolso')['Dias_Atraso'].mean().reset_index()
            df_vintage = df_vintage.rename(columns={'Dias_Atraso': 'Promedio_Dias_Atraso'})
            df_vintage = df_vintage.tail(24)
            
            fig_vintage = px.bar(df_vintage, x='Mes_Desembolso', y='Promedio_Dias_Atraso',
                                 title="Calidad de la Cartera por 'Cosecha' (Vintage)",
                                 labels={'Promedio_Dias_Atraso': 'Promedio de Días de Atraso Actual'})
            st.plotly_chart(fig_vintage, use_container_width=True)

        with col2:
            st.subheader("Proyección de Cartera en Riesgo")
            
            # --- LÍNEA CORREGIDA ---
            riesgo_mensual = df_filtrado.groupby('Mes_Desembolso')['Cartera_Vencida'].sum().reset_index()
            riesgo_mensual = riesgo_mensual.tail(12)

            if len(riesgo_mensual) > 1:
                # --- LÍNEA CORREGIDA ---
                riesgo_mensual['Crecimiento_%'] = riesgo_mensual['Cartera_Vencida'].pct_change().fillna(0)
                tasa_crecimiento_promedio = riesgo_mensual['Crecimiento_%'].mean()

                ultimo_mes = pd.to_datetime(riesgo_mensual['Mes_Desembolso'].max())
                # --- LÍNEA CORREGIDA ---
                ultimo_valor = riesgo_mensual['Cartera_Vencida'].iloc[-1]
                
                proyeccion = []
                for i in range(1, 7):
                    fecha_proyectada = (ultimo_mes + pd.DateOffset(months=i)).strftime('%Y-%m')
                    valor_proyectado = ultimo_valor * ((1 + tasa_crecimiento_promedio) ** i)
                    proyeccion.append({'Mes': fecha_proyectada, 'Valor': valor_proyectado, 'Tipo': 'Proyectado'})
                
                df_proyeccion = pd.DataFrame(proyeccion)
                
                # --- LÍNEA CORREGIDA ---
                riesgo_historico = riesgo_mensual[['Mes_Desembolso', 'Cartera_Vencida']].rename(columns={'Mes_Desembolso': 'Mes', 'Cartera_Vencida': 'Valor'})
                riesgo_historico['Tipo'] = 'Histórico'
                df_grafico_proyeccion = pd.concat([riesgo_historico, df_proyeccion], ignore_index=True)

                fig_proyeccion = px.line(df_grafico_proyeccion, x='Mes', y='Valor', color='Tipo', markers=True,
                                         title="Proyección a 6 Meses de la Cartera en Riesgo",
                                         labels={'Valor': 'Cartera Vencida ($)'}, # <-- Etiqueta corregida también
                                         line_dash='Tipo',
                                         color_discrete_map={'Histórico': 'blue', 'Proyectado': 'red'})
                st.plotly_chart(fig_proyeccion, use_container_width=True)
            else:
                st.warning("No hay suficientes datos históricos para generar una proyección.")

        st.markdown("---")
        st.subheader("Mapa de Calor: Riesgo por Regional y Franja de Mora")
        # --- LÍNEA CORREGIDA ---
        heatmap_data = pd.crosstab(index=df_filtrado['Regional_Venta'], columns=df_filtrado['Franja_Mora'], values=df_filtrado['Cartera_Vencida'], aggfunc='sum').fillna(0)
        # --- LÍNEA CORREGIDA ---
        fig_heatmap = px.imshow(heatmap_data, text_auto=".2s", aspect="auto", labels=dict(x="Franja de Mora", y="Regional de Venta", color="Cartera Vencida"), color_continuous_scale='Reds')
        st.plotly_chart(fig_heatmap, use_container_width=True)


    with tab4:
        st.header("Desempeño por Geografía y Equipos")
        st.info("Visualiza la distribución geográfica de la cartera en un mapa interactivo y analiza el desempeño de los diferentes roles de tu equipo.")

        # --- Mapa de Colombia ---
        st.subheader("Distribución Geográfica del Saldo de Capital por Regional")
        
        geojson_url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e23951b3b18b767808cb536553987178c5e/colombia.geo.json"
        data_mapa = df_filtrado.groupby('Regional_Venta')['Saldo_Capital'].sum().reset_index()
        
        try:
            fig_mapa = px.choropleth_mapbox(
                data_mapa,
                geojson=geojson_url,
                featureidkey="properties.NOMBRE_DPT",
                locations="Regional_Venta",
                color="Saldo_Capital",
                color_continuous_scale="Viridis",
                mapbox_style="carto-positron",
                zoom=4,
                center={"lat": 4.5709, "lon": -74.2973},
                opacity=0.6,
                labels={'Saldo_Capital': 'Saldo de Capital ($)'}
            )
            fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_mapa, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo generar el mapa. Esto puede deberse a que los nombres de 'Regional_Venta' no coinciden con los departamentos. Mostrando gráfico de barras como alternativa.")
            top_regionales = df_filtrado.groupby('Regional_Venta')['Saldo_Capital'].sum().nlargest(15).sort_values()
            fig_regionales_bar = px.bar(top_regionales, orientation='h', text_auto='.2s')
            st.plotly_chart(fig_regionales_bar, use_container_width=True)

        st.markdown("---")
        
        # --- Análisis dinámico de equipos ---
        st.subheader("Análisis de Desempeño por Rol")
        
        rol_seleccionado = st.selectbox(
            "Selecciona un rol para analizar su desempeño:",
            options=['Cobrador', 'Gestor', 'Jefe_ventas', 'Lider_Zona', 'Nombre_Vendedor']
        )
        
        if rol_seleccionado:
            # --- TÍTULO CORREGIDO ---
            st.subheader(f"Top 10 de '{rol_seleccionado}' por Cartera Vencida gestionada")
            
            df_rol = df_filtrado[df_filtrado[rol_seleccionado] != 'NO ESPECIFICADO']
            
            # --- LÍNEA CORREGIDA ---
            top_equipo = df_rol.groupby(rol_seleccionado)['Cartera_Vencida'].sum().nlargest(10).sort_values(ascending=True)
            
            fig_equipo = px.bar(
                top_equipo,
                x=top_equipo.values,
                y=top_equipo.index,
                orientation='h',
                text_auto='.2s',
                title=f"Top 10 '{rol_seleccionado}'"
            )
            # --- ETIQUETA CORREGIDA ---
            fig_equipo.update_layout(xaxis_title="Cartera Vencida ($)", yaxis_title=rol_seleccionado)
            st.plotly_chart(fig_equipo, use_container_width=True)

    with tab5:
        st.header("Explorador y Exportador de Datos Detallados")
        st.info("Interactúa con los datos filtrados: selecciona columnas, ve un resumen estadístico o descarga la información para un análisis externo.")

        # --- Selector de Columnas ---
        st.subheader("1. Selecciona las Columnas a Mostrar")
        todas_las_columnas = df_filtrado.columns.tolist()
        # Definimos una selección por defecto con las columnas más relevantes
        columnas_default = ['Credito', 'Nombre_Cliente', 'Fecha_Desembolso', 'Valor_Desembolso', 'Saldo_Capital', 'Dias_Atraso', 'Franja_Mora', 'Nombre_Vendedor', 'Regional_Venta']
        # Nos aseguramos que las columnas por defecto existan en el dataframe
        columnas_default_existentes = [col for col in columnas_default if col in todas_las_columnas]
        
        columnas_seleccionadas = st.multiselect(
            "Columnas:",
            options=todas_las_columnas,
            default=columnas_default_existentes
        )

        # --- Resumen Estadístico y Descarga ---
        st.subheader("2. Acciones Adicionales")
        col_stats, col_download = st.columns(2)
        
        with col_stats:
            # Checkbox para mostrar el resumen estadístico
            if st.checkbox("Mostrar resumen estadístico"):
                st.write(df_filtrado[columnas_seleccionadas].describe(include='all'))

        with col_download:
            # Botón de descarga
            # Creamos una función para convertir el DF a CSV, requerido por Streamlit
            @st.cache_data
            def convertir_df_a_csv(df):
                return df.to_csv(index=False).encode('utf-8')

            csv = convertir_df_a_csv(df_filtrado[columnas_seleccionadas])
            
            st.download_button(
               label="📥 Descargar datos como CSV",
               data=csv,
               file_name=f'reporte_filtrado_{pd.Timestamp.now().strftime("%Y%m%d")}.csv',
               mime='text/csv',
            )
            
        st.markdown("---")
        
        # --- Mostrar el DataFrame ---
        st.subheader("3. Vista de Datos")
        if not columnas_seleccionadas:
            st.warning("Por favor, selecciona al menos una columna para mostrar la tabla.")
        else:
            st.dataframe(df_filtrado[columnas_seleccionadas])

else:
    st.error("La carga de datos falló. Por favor, revisa el archivo de Excel.")