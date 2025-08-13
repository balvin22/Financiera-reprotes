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

        # El filtro de Empresa no cambia
        empresa = st.sidebar.multiselect(
            "Empresa:",
            options=sorted(df_cartera["Empresa"].unique()),
            default=sorted(df_cartera["Empresa"].unique()),
        )

        # --- FILTROS MODIFICADOS ---
        # 1. Regional ahora es de selección múltiple
        regionales_disponibles = sorted(df_cartera["Regional_Venta"].unique())
        regionales_seleccionadas = st.sidebar.multiselect(
            "Regional:",
            options=regionales_disponibles,
            default=regionales_disponibles
        )

        # 2. Se eliminan Ciudad/Vendedor y se añade Gestor
        gestores_disponibles = sorted(df_cartera["Gestor"].unique())
        gestores_seleccionados = st.sidebar.multiselect(
            "Gestor:",
            options=gestores_disponibles,
            default=gestores_disponibles
        )
        
        # 3. Rodamiento ahora es de selección múltiple y sin 'SIN INFO'
        opciones_rodamiento = sorted([
            r for r in df_cartera["Rodamiento"].unique() if r != 'SIN INFO' and pd.notna(r)
        ])
        rodamiento_seleccionado = st.sidebar.multiselect(
            "Rodamiento:",
            options=opciones_rodamiento,
            default=opciones_rodamiento
        )

        # El filtro de Novedades no cambia
        filtro_novedades = st.sidebar.radio(
            "Novedades:",
            ("Todos", "Con Novedades", "Sin Novedades")
        )

        # --- Lógica de Filtrado Final (ACTUALIZADA) ---
        # Se aplican todos los filtros de selección múltiple a la vez
        df_cartera_filtrada = df_cartera[
            (df_cartera["Empresa"].isin(empresa)) &
            (df_cartera["Regional_Venta"].isin(regionales_seleccionadas)) &
            (df_cartera["Gestor"].isin(gestores_seleccionados)) &
            (df_cartera["Rodamiento"].isin(rodamiento_seleccionado))
        ].copy() # .copy() para evitar advertencias de pandas

        # Se aplica el filtro de Novedades por separado
        if filtro_novedades == "Con Novedades":
            df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] > 0]
        elif filtro_novedades == "Sin Novedades":
            df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] == 0]
        
        # Se actualiza el dataframe de novedades basado en la cartera ya filtrada
        cedulas_filtradas = df_cartera_filtrada["Cedula_Cliente"].unique()
        df_novedades_filtrada = df_novedades[df_novedades["Cedula_Cliente"].isin(cedulas_filtradas)]

        # --- PÁGINA PRINCIPAL ---
        
        tab1, tab2, tab3 = st.tabs([
            "📈 Métricas Principales", 
            "🔄 Análisis de Rodamiento y Recaudos", 
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
            
            # --- KPIs de Rodamiento ---
            col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
            conteo_rodamiento = df_cartera_filtrada["Rodamiento"].value_counts()
            total_creditos_filtrados = len(df_cartera_filtrada)

            def format_metric_value(key):
                count = conteo_rodamiento.get(key, 0)
                percentage = (count / total_creditos_filtrados * 100) if total_creditos_filtrados > 0 else 0
                return f"{count:,} ({percentage:.0f}%)"

            col_r1.metric("✅ Pagaron Total", format_metric_value('PAGO TOTAL'))
            col_r2.metric("👎 Empeoraron", format_metric_value('EMPEORO'))
            col_r3.metric("🎉 Normalizaron", format_metric_value('NORMALIZO'))
            col_r4.metric("👍 Mejoraron", format_metric_value('MEJORO'))
            col_r5.metric("↔️ Se Mantuvieron", format_metric_value('SE MANTIENE'))

            st.markdown("---")

            st.header("Análisis de Recaudos")
            col_rec1, col_rec2 = st.columns(2)
            total_recaudo = df_cartera_filtrada['Total_Recaudo'].sum()
            recaudo_meta = df_cartera_filtrada['Recaudo_Meta'].sum()
            
            col_rec1.metric("💰 Total Recaudado", f"${total_recaudo:,.0f}")
            col_rec2.metric("🎯 Recaudo de Meta", f"${recaudo_meta:,.0f}")

            st.markdown("---")


            st.header("Visualizaciones de Rodamiento y Recaudo")
            
            # --- GRÁFICO DE BARRAS APILADAS CON DIAGNÓSTICOS ---
            
            # 1. Verificación principal: ¿Hay datos después de aplicar los filtros de la sidebar?
            if not df_cartera_filtrada.empty and 'Rodamiento' in df_cartera_filtrada.columns:
                
                df_para_grafico = df_cartera_filtrada[df_cartera_filtrada['Rodamiento'] != 'SIN INFO'].copy()

                # 2. Verificación intermedia: ¿Quedaron datos después de quitar 'SIN INFO'?
                if not df_para_grafico.empty:
                    # Preparación de datos (la lógica es la misma que ya teníamos)
                    df_agrupado = df_para_grafico.groupby(['Franja_Mora', 'Rodamiento']).size().reset_index(name='count')
                    total_por_franja = df_agrupado.groupby('Franja_Mora')['count'].sum().reset_index(name='total')
                    df_final_grafico = pd.merge(df_agrupado, total_por_franja, on='Franja_Mora')
                    df_final_grafico['percentage'] = (df_final_grafico['count'] / df_final_grafico['total']) * 100
                    
                    orden_franjas = ['AL DIA', '1 A 30', '31 A 90', '91 A 180', '181 A 360']
                    df_final_grafico['Franja_Mora'] = pd.Categorical(df_final_grafico['Franja_Mora'], categories=orden_franjas, ordered=True)
                    df_final_grafico.sort_values('Franja_Mora', inplace=True)
                    
                    # 3. Verificación final: ¿La tabla para el gráfico tiene datos?
                    if not df_final_grafico.empty:
                        # Creación del Gráfico
                        fig_rodamiento = px.bar(
                            df_final_grafico,
                            x="Franja_Mora", y="percentage", color="Rodamiento",
                            title="<b>¿Qué pasó con los clientes de cada franja de mora?</b>",
                            labels={'percentage': 'Porcentaje de Clientes (%)', 'Franja_Mora': 'Franja de Mora Inicial'},
                            color_discrete_map={
                                "MEJORO": "green", "NORMALIZO": "blue", "PAGO TOTAL": "skyblue",
                                "SE MANTIENE": "gray", "EMPEORO": "red"
                            },
                            template="plotly_white", custom_data=['count']
                        )
                        fig_rodamiento.update_traces(hovertemplate="<b>%{x}</b><br>Rodamiento: %{fullData.name}<br>Porcentaje: %{y:.2f}%<br><b>Total Créditos: %{customdata[0]:,}</b><extra></extra>")
                        fig_rodamiento.update_layout(yaxis_title="Porcentaje de Clientes (%)")
                        st.plotly_chart(fig_rodamiento, use_container_width=True)
                    else:
                        st.info("No se encontraron datos de rodamiento para graficar con la selección actual.")

                else:
                    st.info("No hay datos de rodamiento (ej. MEJORO, EMPEORO) para mostrar con los filtros actuales. Solo se encontraron categorías no relevantes como 'SIN INFO'.")
            else:
                st.warning("No hay datos de cartera para mostrar en los gráficos con los filtros seleccionados en la barra lateral.")
            
            # --- NUEVO GRÁFICO: Top 10 Gestores por Total Recaudado ---
            if not df_cartera_filtrada.empty:
                recaudo_por_gestor = (
                    df_cartera_filtrada.groupby("Gestor")['Total_Recaudo']
                    .sum()
                    .reset_index()
                    .sort_values(by="Total_Recaudo", ascending=False)
                    .head(10) # Mostramos el Top 10
                )
                
                fig_recaudo_gestor = px.bar(
                    recaudo_por_gestor,
                    x="Gestor",
                    y="Total_Recaudo",
                    title="<b>Top 10 Gestores por Total Recaudado</b>",
                    labels={'Total_Recaudo': 'Recaudo Total ($)', 'Gestor': 'Gestor'},
                    template="plotly_white",
                    text_auto='.2s' # Formato de texto sobre las barras (ej. 1.2M)
                )
                fig_recaudo_gestor.update_traces(textposition='outside')
                st.plotly_chart(fig_recaudo_gestor, use_container_width=True)

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