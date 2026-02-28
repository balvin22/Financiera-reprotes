# ui_components.py
import streamlit as st
import pandas as pd
import numpy as np

def inject_custom_css():
    """Inyecta CSS para estilizar el botón de limpiar filtros y ajustar márgenes."""
    st.markdown("""
        <style>
        .stButton>button {
            color: #d9534f !important;
            border-color: #d9534f !important;
            background-color: transparent !important;
            font-weight: bold;
            border-radius: 20px;
        }
        .stButton>button:hover {
            background-color: #d9534f !important;
            color: white !important;
        }
        .filter-title {
            font-size: 13px;
            font-weight: bold;
            color: #555566;
            margin-bottom: 5px;
            margin-top: 15px;
            letter-spacing: 1px;
        }
        </style>
    """, unsafe_allow_html=True)

def render_checkbox_group(title, options, prefix, height=180):
    st.sidebar.markdown(f"<div class='filter-title'>{title}</div>", unsafe_allow_html=True)
    selected_options = []
    
    with st.sidebar.container(height=height, border=True):
        for opt in options:
            key = f"chk_{prefix}_{opt}"
            if key not in st.session_state:
                st.session_state[key] = False
            if st.checkbox(str(opt), key=key):
                selected_options.append(opt)
                
    return selected_options

def clear_all_filters_callback():
    """Recorre la sesión y apaga todos los checkboxes antes de redibujar."""
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"):
            st.session_state[key] = False
    if "rad_novedades" in st.session_state:
        st.session_state["rad_novedades"] = "Todos"

def sidebar_filters(df):
    """Crea y devuelve los filtros de la barra lateral con el nuevo diseño UI."""
    inject_custom_css()
    
    col_icon, col_text = st.sidebar.columns([1, 4])
    with col_icon:
        st.markdown("<h2 style='margin:0; padding:0; color:#3b3b6d;'>⚗️</h2>", unsafe_allow_html=True)
    with col_text:
        st.markdown("<h2 style='margin:0; padding:0; color:#3b3b6d;'>Filtros</h2>", unsafe_allow_html=True)
        
    st.sidebar.markdown("<p style='font-size: 12px; color: gray; margin-bottom: 20px;'>No selecciones nada para ver todas las opciones.</p>", unsafe_allow_html=True)
    
    filters = {}
    
    # 1. EMPRESA
    opciones_empresa = sorted(df["Empresa"].unique())
    h_emp = 100 if len(opciones_empresa) <= 2 else 180
    filters['empresa'] = render_checkbox_group("🏢 EMPRESA", opciones_empresa, "empresa", height=h_emp)
    
    # 2. CALL CENTER
    if 'CALL_CENTER_FILTRO' in df.columns:
        opciones_brutas = df['CALL_CENTER_FILTRO'].unique()
        opciones_call_center = sorted([opc for opc in opciones_brutas if opc != 'SIN CALL CENTER'])
        filters['call_center'] = render_checkbox_group("🎧 CALL CENTER", opciones_call_center, "cc")
    else:
        filters['call_center'] = []

    # 3. ZONA
    if 'Zona' in df.columns:
        df['Zona'] = df['Zona'].fillna('SIN ZONA')
        opciones_zona = sorted(df["Zona"].unique())
        filters['Zona'] = render_checkbox_group("📍 ZONA", opciones_zona, "zona")
    else:
        filters['Zona'] = []

    # 4. REGIONAL DE COBRO
    if 'Regional_Cobro' in df.columns:
        df['Regional_Cobro'] = df['Regional_Cobro'].replace(np.nan, 'OTRAS ZONAS')
        df['Regional_Cobro'] = df['Regional_Cobro'].replace('nan', 'OTRAS ZONAS')
        opciones_regional_cobro = sorted(df["Regional_Cobro"].unique())
        filters['regional_cobro'] = render_checkbox_group("🗺️ REGIONAL", opciones_regional_cobro, "reg")
    else:
        filters['regional_cobro'] = []

    # 5. FRANJA CARTERA
    if 'Franja_Cartera' in df.columns:
        opciones_franja = sorted(df["Franja_Cartera"].unique())
        filters['franja_cartera'] = render_checkbox_group("📊 FRANJA DE CARTERA", opciones_franja, "franja")
    else:
        filters['franja_cartera'] = []
        
    # 6. ESTADO DE VIGENCIA (NUEVO FILTRO)
    opciones_vigencia = ["Vigentes", "Anticipados", "Vencidos"]
    # Usamos height=130 para que queden justas las 3 opciones sin que sobre espacio
    filters['vigencia'] = render_checkbox_group("⏳ ESTADO DE VIGENCIA", opciones_vigencia, "vig", height=130)
    
    st.sidebar.markdown("<hr style='margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
    
    # 7. ESTADO NOVEDADES 
    if "rad_novedades" not in st.session_state:
        st.session_state["rad_novedades"] = "Todos"
        
    st.sidebar.markdown("<div class='filter-title'>📋 ESTADO NOVEDADES</div>", unsafe_allow_html=True)
    filters['novedades'] = st.sidebar.radio(
        "",
        ("Todos", "Con Novedades", "Sin Novedades"),
        key="rad_novedades",
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    st.sidebar.button("Limpiar Filtros", use_container_width=True, on_click=clear_all_filters_callback)
        
    return filters

def display_detailed_data(df, title, default_cols):
    col_header, col_count = st.columns([3, 1])
    with col_header:
        st.subheader(title)
    with col_count:
        st.markdown(f"<div style='text-align: right; padding-top: 10px; color: gray;'>Total: <b>{len(df):,}</b></div>", unsafe_allow_html=True)
    
    all_columns = df.columns.tolist()
    
    with st.expander(f"Personalizar columnas de: {title}", expanded=False):
        unique_key = f"multiselect_{title.replace(' ', '_').lower()}"
        selected_columns = st.multiselect(
            "Selecciona las columnas visibles:",
            options=all_columns,
            default=[col for col in default_cols if col in all_columns],
            key=unique_key,
            label_visibility="collapsed"
        )
    
    if selected_columns:
        df_visible = df[selected_columns]
        st.data_editor(df_visible, use_container_width=True, hide_index=True, disabled=True, key=f"editor_{unique_key}")
        return df_visible
    else:
        st.warning("⚠️ Por favor selecciona al menos una columna para visualizar la tabla.")
        return None