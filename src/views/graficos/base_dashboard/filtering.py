import numpy as np

def apply_main_filters(df_cartera, df_novedades, filters):
    """
    Aplica los filtros de la barra lateral a los dataframes de cartera y novedades.
    """
    df_cartera_filtrada = df_cartera[
        df_cartera["Empresa"].isin(filters['empresa']) &
        df_cartera["Regional_Cobro"].isin(filters['regional_cobro']) &
        df_cartera["Franja_Cartera"].isin(filters['franja_cartera']) &
        df_cartera["Zona"].isin(filters['Zona']) &
        df_cartera["CALL_CENTER_FILTRO"].isin(filters.get('call_center', df_cartera["CALL_CENTER_FILTRO"].unique()))
    ].copy()

    if filters['novedades'] == "Con Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] > 0]
    elif filters['novedades'] == "Sin Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] == 0]

    cedulas_filtradas = df_cartera_filtrada["Cedula_Cliente"].unique()
    df_novedades_filtrada = df_novedades[df_novedades["Cedula_Cliente"].isin(cedulas_filtradas)]

    return df_cartera_filtrada, df_novedades_filtrada


def add_call_center_column(df):
    """
    Crea una nueva columna 'CALL_CENTER_FILTRO' unificando los valores
    de 'Zona' (para CL1-CL4) y 'Call_Center_Apoyo' (para CL5-CL9).
    """
    df_copy = df.copy()

    if 'Zona' not in df_copy.columns:
        df_copy['Zona'] = ''
    if 'Call_Center_Apoyo' not in df_copy.columns:
        df_copy['Call_Center_Apoyo'] = ''
        
    # Rellenar NaNs con strings vacíos para que isin funcione correctamente
    df_copy['Zona'] = df_copy['Zona'].fillna('')
    df_copy['Call_Center_Apoyo'] = df_copy['Call_Center_Apoyo'].fillna('')

    conditions = [
        df_copy['Zona'].isin(['CL1', 'CL2', 'CL3', 'CL4']),
        df_copy['Call_Center_Apoyo'].isin(['CL5', 'CL6', 'CL7', 'CL8', 'CL9'])
    ]
    choices = [
        df_copy['Zona'],
        df_copy['Call_Center_Apoyo']
    ]
    
    # Usamos np.select para aplicar la lógica condicional de forma eficiente
    df_copy['CALL_CENTER_FILTRO'] = np.select(conditions, choices, default='SIN CALL CENTER')
    
    return df_copy
