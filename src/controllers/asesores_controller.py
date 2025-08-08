from src.services.asesores.asesores_services import LoaderService

# 1. Crear una instancia del servicio
servicio_carga = LoaderService()

# 2. Definir rutas a los archivos
RUTA_ARCHIVO_VENTAS = 'c:/Users/usuario/Desktop/Reportes Soraya/CV0018.XLSX'
RUTA_ARCHIVO_ASESORES = 'c:/Users/usuario/Desktop/JULIO/ASESORES ACTIVOS (1).xlsx'
RUTA_ARCHIVO_SALIDA = 'reporte_final_consolidado.xlsx'


# 3. Usar el servicio para cargar cada archivo con su configuración
def main():
    """
    Función principal que orquesta la generación del reporte.
    """
    print("🚀 Iniciando el proceso de generación de reporte...")

    # 1. Se instancia el servicio principal que contiene toda la lógica.
    servicio_reporte = LoaderService()

    # 2. Se llama al método que ejecuta todos los pasos.
    #    Toda la complejidad está oculta dentro de este método.
    exito = servicio_reporte.generar_reporte_completo(
        path_ventas=RUTA_ARCHIVO_VENTAS,
        path_asesores=RUTA_ARCHIVO_ASESORES,
        path_salida=RUTA_ARCHIVO_SALIDA
    )

    # 3. Se informa el resultado final.
    if exito:
        print(f"✅ ¡Reporte generado exitosamente en: '{RUTA_ARCHIVO_SALIDA}'!")
    else:
        print("❌ El reporte no pudo ser generado debido a errores previos.")

if __name__ == "__main__":
    main()