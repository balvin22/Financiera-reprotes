import pandas as pd
# Importamos nuestro modelo de configuración
from src.models.financiera_model import configuracion

class LoaderService:
    """
    Servicio encargado de orquestar todo el proceso de carga,
    procesamiento y generación del reporte financiero con múltiples hojas.
    """
    def __init__(self):
        self.config = configuracion
        print("LoaderService inicializado.")

    def _cargar_un_archivo(self, clave_config: str, ruta_archivo: str):
        # (Este método no necesita cambios, se mantiene igual)
        if clave_config not in self.config:
            print(f"❌ Error: La clave '{clave_config}' no existe en la configuración.")
            return None
        config_especifica = self.config[clave_config]
        columnas_a_usar = config_especifica['usecols']
        mapa_renombre = config_especifica['rename_map']
        nombre_hoja = config_especifica.get('sheet_name', 0)
        header_row = config_especifica.get('header', 0)
        try:
            df = pd.read_excel(
                ruta_archivo,
                sheet_name=nombre_hoja,
                header=header_row,
                usecols=columnas_a_usar
            )
            df_procesado = df.rename(columns=mapa_renombre)
            print(f"✅ Archivo '{ruta_archivo}' (Hoja: '{nombre_hoja}') cargado exitosamente.")
            return df_procesado
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado al procesar '{ruta_archivo}': {e}")
            return None

    def _crear_tabla_pivote(self, df_input: pd.DataFrame) -> pd.DataFrame:
        """
        Función auxiliar para crear la tabla pivote.
        Agrupa los datos y añade la columna de Rango de ventas.
        """
        if df_input.empty:
            return pd.DataFrame()

        # 1. Crear la tabla pivote como antes
        df_pivot = pd.pivot_table(
            df_input,
            index=['Regional', 'Cedula_Asesor', 'Nombre_Asesor', 'Tipo_Asesor'],
            columns='Forma_Pago',
            values='Ventas_Antes_Iva',
            aggfunc='sum',
            fill_value=0
        )
        
        # 2. Calcular el Total General como antes
        df_pivot['Total_General'] = df_pivot.sum(axis=1)
        
        # --- 3. LÓGICA CORREGIDA: Ajustar los rangos para incluir cero y negativos ---
    
        # Definimos los límites (empezamos desde -infinito para capturar todo)
        bins = [-float('inf'), 0, 5999999, 15999999, 20999999, 40999999, 60999999, 80999999, float('inf')]
        
        # Definimos las etiquetas (añadimos una etiqueta para el nuevo rango)
        labels = [
            "Sin Ventas o Negativo", # <-- NUEVA ETIQUETA
            "0 a 5 Millones",
            "6 a 15 Millones",
            "16 a 20 Millones",
            "21 a 40 Millones",
            "41 a 60 Millones",
            "61 a 80 Millones",
            "Más de 80 Millones"
        ]
        
        df_pivot['Rango'] = pd.cut(
            df_pivot['Total_General'],
            bins=bins,
            labels=labels,
            right=True  # Usamos right=True para que el 0 se incluya en la primera categoría
        )
        
        # 4. Convertir el índice en columnas como antes
        return df_pivot.reset_index()

    def generar_reporte_completo(self, path_ventas: str, path_asesores: str, path_salida: str) -> bool:
        """
        (Método principal) Carga los datos, los segmenta y guarda un
        reporte con 4 hojas, incluyendo un resumen regional solo de asesores.
        """
        # --- PASO 1 y 2 (Sin cambios) ---
        print("\n--- Iniciando Carga de Datos ---")
        df_ventas = self._cargar_un_archivo("CV0018", path_ventas)
        df_asesores_data = self._cargar_un_archivo("ASESORES", path_asesores) # Renombrado para evitar confusión

        if df_ventas is None or df_asesores_data is None:
            return False

        print("\n--- Iniciando Procesamiento y Lógica de Negocio ---")
        try:
            df_consolidado = pd.merge(df_ventas, df_asesores_data, on='Cedula_Asesor', how='left')

            print("Segmentando datos para cada hoja del reporte...")
            filtro_corretaje = df_consolidado['Tipo_Asesor'] == 'CORRETAJE'
            df_corretaje = df_consolidado[filtro_corretaje]

            filtro_asesores = (df_consolidado['Tipo_Asesor'] != 'CORRETAJE') & (df_consolidado['Tipo_Asesor'].notna())
            df_asesores_filtrado = df_consolidado[filtro_asesores]

            filtro_sin_registrar = df_consolidado['Tipo_Asesor'].isna()
            df_sin_registrar = df_consolidado[filtro_sin_registrar].copy()

            # --- PASO 3: PREPARAR LOS REPORTES INDIVIDUALES ---
            print("Generando tablas pivote y reportes finales...")
            df_sin_registrar.loc[:, 'Tipo_Asesor'] = 'SIN REGISTRAR'
            df_sin_registrar.loc[:, 'Nombre_Asesor'] = df_sin_registrar['Nombre_Asesor'].fillna(df_sin_registrar['Cedula_Asesor'])

            reporte_corretaje = self._crear_tabla_pivote(df_corretaje)
            reporte_asesores = self._crear_tabla_pivote(df_asesores_filtrado)
            reporte_sin_registrar = self._crear_tabla_pivote(df_sin_registrar)

            # --- PASO 3.5: PREPARAR REPORTE DE RESUMEN REGIONAL (LÓGICA NUEVA) ---
            print("Generando hoja de resumen regional a partir de la hoja 'asesores'...")
            
            # 1. Crear el cuerpo de la tabla pivote USANDO SOLO 'reporte_asesores'
            reporte_resumen = pd.pivot_table(
                reporte_asesores,  # <-- CAMBIO CLAVE: Usamos el reporte de asesores como fuente
                index='Regional',
                columns='Rango',
                values='Cedula_Asesor',
                aggfunc='nunique',
                fill_value=0,
                observed=False
            )
            
            # 2. Calcular el 'Total General' HORIZONTAL
            reporte_resumen['Total General'] = reporte_resumen.sum(axis=1).astype(int)
            
            # 3. Calcular el 'Total General' VERTICAL
            reporte_resumen.loc['Total General'] = reporte_resumen.sum(axis=0).astype(int)
            
            # 4. Convertir el índice en una columna normal
            reporte_resumen = reporte_resumen.reset_index()

        except Exception as e:
            print(f"❌ Error durante el procesamiento de datos: {e}")
            return False

        # --- PASO 4: GUARDAR EL REPORTE CON MÚLTIPLES HOJAS ---
        print("\n--- Guardando el Reporte Final con 4 Hojas ---")
        try:
            with pd.ExcelWriter(path_salida, engine='openpyxl') as writer:
                reporte_resumen.to_excel(writer, sheet_name='Resumen Regional', index=False)
                reporte_corretaje.to_excel(writer, sheet_name='corretaje', index=False)
                reporte_asesores.to_excel(writer, sheet_name='asesores', index=False)
                reporte_sin_registrar.to_excel(writer, sheet_name='sin registrar', index=False)
            
            print(f"✅ Reporte con 4 hojas generado exitosamente en: '{path_salida}'")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar el archivo Excel: {e}")
            return False