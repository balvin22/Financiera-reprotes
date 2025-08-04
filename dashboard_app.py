# dashboard_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="📊",
    layout="wide"
)

# --- DATOS DE EJEMPLO (Simulando la carga desde un CSV) ---
# En un caso real, usarías pd.read_csv('tu_archivo.csv')
@st.cache_data # Usamos el caché de Streamlit para no recargar los datos en cada interacción
def cargar_datos():
    csv_data = """Fecha,Producto,Categoría,Unidades Vendidas,Precio Unitario
2024-07-01,El Quijote,Ficción,5,25.50
2024-07-01,Cien Años de Soledad,Ficción,3,22.00
2024-07-01,Álgebra de Baldor,Educación,10,35.00
2024-07-02,El Quijote,Ficción,2,25.50
2024-07-02,Python para Todos,Educación,7,40.10
2024-07-03,Cien Años de Soledad,Ficción,4,22.00
2024-07-03,Cosmos,Ciencia,6,30.00
2024-07-04,Álgebra de Baldor,Educación,8,35.00
2024-07-04,Sapiens,Ciencia,5,28.75
2024-07-05,Python para Todos,Educación,9,40.10
2024-07-05,Cosmos,Ciencia,4,30.00
"""
    # Usamos io.StringIO para leer el string como si fuera un archivo
    dataframe = pd.read_csv(io.StringIO(csv_data))
    
    # --- Transformación de Datos con Pandas ---
    dataframe['Fecha'] = pd.to_datetime(dataframe['Fecha'])
    dataframe['Ingresos'] = dataframe['Unidades Vendidas'] * dataframe['Precio Unitario']
    return dataframe

df = cargar_datos()

# --- TÍTULO Y DESCRIPCIÓN ---
st.title("📊 Dashboard de Ventas Interactivo")
st.markdown("Este dashboard permite explorar los datos de ventas de una librería.")

# --- BARRA LATERAL (SIDEBAR) PARA FILTROS ---
st.sidebar.header("Filtros Disponibles")

# Filtro por categoría de producto
categorias = df['Categoría'].unique()
categoria_seleccionada = st.sidebar.multiselect(
    "Selecciona una o varias categorías:",
    options=categorias,
    default=categorias  # Por defecto, todas las categorías están seleccionadas
)

# --- FILTRADO DE DATOS (PANDAS) ---
# Si no se selecciona ninguna categoría, usamos el DataFrame completo
if not categoria_seleccionada:
    df_filtrado = df.copy()
else:
    df_filtrado = df[df['Categoría'].isin(categoria_seleccionada)]


# --- PÁGINA PRINCIPAL ---

# Métricas principales (KPIs)
total_ingresos = int(df_filtrado['Ingresos'].sum())
total_unidades_vendidas = int(df_filtrado['Unidades Vendidas'].sum())

# Usamos columnas para mostrar las métricas lado a lado
col1, col2 = st.columns(2)
with col1:
    st.metric("Ingresos Totales", f"${total_ingresos:,}")
with col2:
    st.metric("Total de Unidades Vendidas", f"{total_unidades_vendidas:,}")

st.markdown("---") # Línea divisoria

# --- GRÁFICOS (PLOTLY) ---

# Gráfico de barras: Ingresos por Producto
ingresos_por_producto = df_filtrado.groupby('Producto')['Ingresos'].sum().sort_values(ascending=False)

fig_barras = px.bar(
    ingresos_por_producto,
    x=ingresos_por_producto.values,
    y=ingresos_por_producto.index,
    orientation='h',
    title="<b>Ingresos por Producto</b>",
    template="plotly_white",
    labels={'x': 'Ingresos ($)', 'y': 'Producto'}
)
fig_barras.update_layout(plot_bgcolor="rgba(0,0,0,0)")

# Gráfico de líneas: Ingresos a lo largo del tiempo
ingresos_por_fecha = df_filtrado.groupby('Fecha')['Ingresos'].sum().reset_index()

fig_lineas = px.line(
    ingresos_por_fecha,
    x='Fecha',
    y='Ingresos',
    title="<b>Evolución de Ingresos</b>",
    template="plotly_white"
)
fig_lineas.update_layout(plot_bgcolor="rgba(0,0,0,0)")


# Mostramos los gráficos en columnas
col_graf1, col_graf2 = st.columns(2)
with col_graf1:
    st.plotly_chart(fig_barras, use_container_width=True)
with col_graf2:
    st.plotly_chart(fig_lineas, use_container_width=True)


# --- TABLA DE DATOS ---
st.subheader("Datos Detallados")
st.dataframe(df_filtrado)