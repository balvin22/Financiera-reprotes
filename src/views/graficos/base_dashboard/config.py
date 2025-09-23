# config.py

# Define el orden lógico de las franjas de mora
ORDEN_FRANJAS = ['AL DIA', '1 A 30', '31 A 90', '91 A 180', '181 A 360', 'MAS DE 360']

# Mapeo para agrupar las zonas de cobro
ZONA_COBRO_MAP = {
    'ZCN': 'CASA COBRANZA',
    '1AB': 'ABOGADO',
    'CC01': 'CASTIGO',
    '1CE': 'OTROS CASOS',
    'CEC': 'OTROS CASOS'
}

# Columnas a mostrar por defecto en la tabla de cartera
COLUMNAS_DEFECTO_CARTERA = [
    'Credito', 'Cedula_Cliente', 'Nombre_Cliente', 'Empresa',
    'Saldo_Capital', 'Dias_Atraso', 'Franja_Meta', 'Rodamiento',
    'Franja_Meta_Final', 'Cantidad_Novedades', 'Fecha_Ultima_Novedad'
]