def apply_main_filters(df_cartera, df_novedades, filters):
    """
    Aplica los filtros de la barra lateral a los dataframes de cartera y novedades.

    Args:
        df_cartera (pd.DataFrame): El dataframe principal de cartera.
        df_novedades (pd.DataFrame): El dataframe de novedades.
        filters (dict): Un diccionario con los valores de los filtros de la sidebar.

    Returns:
        tuple: Un tuple conteniendo df_cartera_filtrada y df_novedades_filtrada.
    """
    df_cartera_filtrada = df_cartera[
        df_cartera["Empresa"].isin(filters['empresa']) &
        df_cartera["Regional_Cobro"].isin(filters['regional_cobro']) &
        df_cartera["Franja_Cartera"].isin(filters['franja_cartera']) &
        df_cartera["Zona"].isin(filters['Zona'])
    ].copy()

    # Filtro de novedades
    if filters['novedades'] == "Con Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] > 0]
    elif filters['novedades'] == "Sin Novedades":
        df_cartera_filtrada = df_cartera_filtrada[df_cartera_filtrada["Cantidad_Novedades"] == 0]

    # Filtrar novedades basado en las cédulas de la cartera ya filtrada
    cedulas_filtradas = df_cartera_filtrada["Cedula_Cliente"].unique()
    df_novedades_filtrada = df_novedades[df_novedades["Cedula_Cliente"].isin(cedulas_filtradas)]

    return df_cartera_filtrada, df_novedades_filtrada
