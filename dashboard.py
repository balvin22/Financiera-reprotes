import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Necesario para el gráfico Sankey

@st.cache_data # Este decorador acelera la carga del archivo
def load_data(uploaded_file):
    """
    Carga y procesa los datos desde el archivo Excel subido, devolviendo dos DataFrames.
    """
    print("Cargando y procesando archivo...")
    df_cartera = pd.read_excel(uploaded_file, sheet_name="Analisis_de_Cartera")
    df_novedades = pd.read_excel(uploaded_file, sheet_name="Detalle_Novedades")

    # --- Limpieza y conversión de tipos de datos ---
    for col in ["Fecha_Desembolso", "Fecha_Ultima_Novedad"]:
        if col in df_cartera.columns:
            df_cartera[col] = pd.to_datetime(df_cartera[col], errors="coerce").dt.date

    if "Fecha_Novedad" in df_novedades.columns:
        df_novedades["Fecha_Novedad"] = pd.to_datetime(df_novedades["Fecha_Novedad"], errors="coerce").dt.date

    for col in ["Empresa", "Regional_Venta", "Nombre_Ciudad", "Nombre_Vendedor", "Franja_Mora", "Rodamiento"]:
        if col in df_cartera.columns:
            df_cartera[col] = df_cartera[col].astype(str)

    if "Cantidad_Novedades" in df_cartera.columns:
        df_cartera['Cantidad_Novedades'] = pd.to_numeric(df_cartera['Cantidad_Novedades'], errors='coerce').fillna(0)
        
    print("Carga completada.")
    return df_cartera, df_novedades

def main():
    """
    Función principal que construye el dashboard de Streamlit.
    """
    st.set_page_config(layout="wide")
    st.title("📊 Dashboard de Información de Cartera")

    # --- Carga de Archivo en la Barra Lateral ---
    st.sidebar.header("Cargar Archivo")
    uploaded_file = st.sidebar.file_uploader(
        "Cargar tu reporte (ej: Reporte_Novedades_y_Analisis.xlsx)", 
        type=["xlsx"]
    )

    if uploaded_file is None:
        st.info("Por favor, carga tu archivo de reporte en formato .xlsx para comenzar.")
        return

    try:
        df_cartera, df_novedades = load_data(uploaded_file)

        # --- Filtros en la Barra Lateral ---
        st.sidebar.header("Filtros de Cartera")
        empresa = st.sidebar.multiselect(
            "Empresa:",
            options=sorted(df_cartera["Empresa"].unique()),
            default=sorted(df_cartera["Empresa"].unique()),
        )

        # --- Filtros Anidados (REGIONAL -> CIUDAD -> VENDEDOR) ---
        lista_regionales = ['Todas'] + sorted(df_cartera["Regional_Venta"].unique())
        regional_seleccionada = st.sidebar.selectbox("Regional:", options=lista_regionales)

        df_filtrado_regional = df_cartera[df_cartera["Regional_Venta"] == regional_seleccionada] if regional_seleccionada != "Todas" else df_cartera

        ciudades_disponibles = sorted(df_filtrado_regional["Nombre_Ciudad"].unique())
        ciudad_seleccionada = st.sidebar.multiselect("Ciudad:", options=ciudades_disponibles, default=ciudades_disponibles)
        
        df_filtrado_ciudad = df_filtrado_regional[df_filtrado_regional["Nombre_Ciudad"].isin(ciudad_seleccionada)]

        vendedores_disponibles = sorted(df_filtrado_ciudad["Nombre_Vendedor"].unique())
        vendedor_seleccionado = st.sidebar.multiselect("Vendedor:", options=vendedores_disponibles, default=vendedores_disponibles)

        # --- Filtros Adicionales ---
        filtro_novedades = st.sidebar.radio("Novedades:", ("Todos", "Con Novedades", "Sin Novedades"))
        
        opciones_rodamiento = ['Todos'] + sorted(df_cartera["Rodamiento"].unique())
        filtro_rodamiento = st.sidebar.selectbox("Rodamiento:", options=opciones_rodamiento)

        # --- Lógica de Filtrado Final ---
        df_cartera_filtrada = df_cartera[
            (df_cartera["Empresa"].isin(empresa)) &
            (df_cartera["Nombre_Ciudad"].isin(ciudad_seleccionada)) &
            (df_cartera["Nombre_Vendedor"].isin(vendedor_seleccionado))
        ]
        if regional_seleccionada != "Todas":
            df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Regional_Venta"] == regional_seleccionada]
        if filtro_novedades == "Con Novedades":
            df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] > 0]
        elif filtro_novedades == "Sin Novedades":
            df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] == 0]
        if filtro_rodamiento != "Todos":
            df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Rodamiento"] == filtro_rodamiento]
        
        cedulas_filtradas = df_cartera_filtrada["Cedula_Cliente"].unique()
        df_novedades_filtrada = df_novedades[df_novedades["Cedula_Cliente"].isin(cedulas_filtradas)]

        # --- PÁGINA PRINCIPAL ---
        
        tab1, tab2, tab3 = st.tabs([
            "📈 Métricas Principales", 
            "🔄 Análisis de Rodamiento", 
            "📄 Datos Detallados"
        ])

        # --- PESTAÑA 1: MÉTRICAS PRINCIPALES ---
        with tab1:
            st.header("Métricas Principales del Periodo")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Valor Desembolsado", f"${df_cartera_filtrada['Valor_Desembolso'].sum():,.0f}")
            col2.metric("💼 Saldo de Capital", f"${df_cartera_filtrada['Saldo_Capital'].sum():,.0f}")
            col3.metric("⏳ Días Atraso Prom.", f"{df_cartera_filtrada['Dias_Atraso'].mean():.1f}")
            col4.metric("📄 Total Créditos", f"{len(df_cartera_filtrada):,}")
            st.markdown("---")
            st.header("Visualizaciones Generales")
            
            col_g1, col_g2 = st.columns(2)
            if not df_cartera_filtrada.empty:
                # Gráfico de Franja de Mora
                franja_mora = df_cartera_filtrada["Franja_Mora"].value_counts().reset_index()
                fig_franja_mora = px.pie(franja_mora, values="count", names="Franja_Mora", title="<b>Distribución por Franja de Mora</b>", hole=0.4)
                col_g1.plotly_chart(fig_franja_mora, use_container_width=True)
                
                # Gráfico de Tipos de Novedades
                if not df_novedades_filtrada.empty:
                    tipos_novedad = df_novedades_filtrada["Tipo_Novedad"].value_counts().reset_index()
                    fig_novedades = px.bar(tipos_novedad, x="Tipo_Novedad", y="count", title="<b>Top Tipos de Novedades</b>")
                    col_g2.plotly_chart(fig_novedades, use_container_width=True)
            
            # ... (Aquí puedes poner otros gráficos generales como el de desembolsos en el tiempo) ...

        # --- PESTAÑA 2: ANÁLISIS DE RODAMIENTO ---
        with tab2:
            st.header("Análisis de Rodamiento de Cartera")
            st.header("Análisis de Rodamiento")
            col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        
            # 1. Obtenemos el conteo para cada categoría
            conteo_rodamiento = df_cartera_filtrada["Rodamiento"].value_counts()
            
            # 2. Obtenemos el TOTAL de créditos que se están mostrando (después de filtros)
            total_creditos_filtrados = len(df_cartera_filtrada)

            # 3. Función auxiliar para calcular y formatear el texto
            def format_metric_value(key):
                count = conteo_rodamiento.get(key, 0)
                # Evitamos errores si el total es 0
                percentage = (count / total_creditos_filtrados * 100) if total_creditos_filtrados > 0 else 0
                # Formateamos el texto como "1,234 (15%)"
                return f"{count:,} ({percentage:.0f}%)"

            # 4. Asignamos los valores formateados a cada métrica
            col_r1.metric("✅ Pagaron Total", format_metric_value('PAGO TOTAL'))
            col_r2.metric("👎 Empeoraron", format_metric_value('EMPEORO'))
            col_r3.metric("🎉 Normalizaron", format_metric_value('NORMALIZO'))
            col_r4.metric("👍 Mejoraron", format_metric_value('MEJORO'))
            col_r5.metric("↔️ Se Mantuvieron", format_metric_value('SE MANTIENE'))

            st.markdown("---")
            st.header("Visualizaciones de Rodamiento")
            
            # Gráfico de Barras Apiladas de Rodamiento
            if not df_cartera_filtrada.empty and 'Rodamiento' in df_cartera_filtrada.columns:

            # --- 1. PREPARACIÓN DE DATOS (MODIFICADO) ---
            
            # a) Filtrar para ignorar la categoría 'SIN INFO' del análisis
                df_para_grafico = df_cartera_filtrada[df_cartera_filtrada['Rodamiento'] != 'SIN INFO'].copy()

                # b) Crear la tabla pivote con los datos ya filtrados
                rodamiento_pivot = pd.crosstab(
                    index=df_para_grafico['Franja_Mora'], 
                    columns=df_para_grafico['Rodamiento'], 
                    normalize='index'
                ) * 100
                
                # c) Definir y aplicar el orden correcto para las franjas (eje X)
                orden_franjas = ['AL DIA', '1 A 30', '31 A 90', '91 A 180', '181 A 360']
                # Reordenamos el índice de la tabla pivote según nuestra lista
                rodamiento_pivot = rodamiento_pivot.reindex(
                    [franja for franja in orden_franjas if franja in rodamiento_pivot.index]
                )

                # d) Reordenar las columnas (leyenda) para una mejor visualización
                column_order = ['MEJORO', 'NORMALIZO', 'PAGO TOTAL', 'SE MANTIENE', 'EMPEORO']
                rodamiento_pivot = rodamiento_pivot.reindex(
                    columns=[col for col in column_order if col in rodamiento_pivot.columns]
                )

                # --- 2. CREACIÓN DEL GRÁFICO (La llamada no cambia) ---
                fig_rodamiento = px.bar(
                    rodamiento_pivot,
                    x=rodamiento_pivot.index,
                    y=rodamiento_pivot.columns,
                    title="<b>¿Qué pasó con los clientes de cada franja de mora?</b>",
                    labels={'value': 'Porcentaje de Clientes (%)', 'Franja_Mora': 'Franja de Mora Inicial'},
                    color_discrete_map={
                        "MEJORO": "green",
                        "NORMALIZO": "blue",
                        "PAGO TOTAL": "skyblue",
                        "SE MANTIENE": "gray",
                        "EMPEORO": "red"
                    },
                    template="plotly_white"
                )
                
                fig_rodamiento.update_layout(yaxis_title="Porcentaje de Clientes (%)")
                st.plotly_chart(fig_rodamiento, use_container_width=True)

        # --- PESTAÑA 3: DATOS DETALLADOS ---
        with tab3:
            st.header("Explorador de Datos Detallados")

            # --- Selector de columnas para la tabla de Cartera ---
            st.subheader("Análisis de Cartera (Filtrado)")
            
            todas_las_columnas = df_cartera_filtrada.columns.tolist()
            # Define las columnas que quieres mostrar por defecto
            columnas_por_defecto = [
                'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Empresa', 
                'Saldo_Capital', 'Dias_Atraso', 'Franja_Mora', 'Rodamiento', 
                'Franja_Mora_Final', 'Cantidad_Novedades', 'Fecha_Ultima_Novedad'
            ]
            
            columnas_seleccionadas = st.multiselect(
                "Selecciona las columnas a mostrar en la tabla de Cartera:",
                options=todas_las_columnas,
                default=[col for col in columnas_por_defecto if col in todas_las_columnas]
            )
            if columnas_seleccionadas:
                st.dataframe(df_cartera_filtrada[columnas_seleccionadas])

            st.markdown("---")

            # --- Selector de columnas para la tabla de Novedades ---
            st.subheader("Detalle de Novedades (Filtrado)")
            if not df_novedades_filtrada.empty:
                columnas_novedades = df_novedades_filtrada.columns.tolist()
                columnas_seleccionadas_nov = st.multiselect(
                    "Selecciona las columnas a mostrar en la tabla de Novedades:",
                    options=columnas_novedades,
                    default=columnas_novedades # Muestra todas por defecto
                )
                if columnas_seleccionadas_nov:
                    st.dataframe(df_novedades_filtrada[columnas_seleccionadas_nov])

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo. Error: {e}")

if __name__ == "__main__":
    main()