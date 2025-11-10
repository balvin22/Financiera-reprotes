import time

# --- 1. CONFIGURACIÓN DE ARCHIVOS ---
# Archivo principal (el que quieres limpiar)
archivo_principal = 'c:/Users/usuario/Downloads/USU10791_20251110 CLIENTES.txt'

# Archivo con los registros que quieres eliminar
archivo_a_quitar = 'c:/Users/usuario/Downloads/USU10791_20251105 CLIENTES.txt'

# Archivo donde se guardará el resultado limpio
archivo_salida = 'CLIENTES_FILTRADOS.txt'

print("--- Iniciando proceso de limpieza ---")
start_time = time.time()

try:
    # --- 2. Cargar los registros a eliminar en un set (para velocidad) ---
    print(f"Cargando líneas a eliminar desde '{archivo_a_quitar}'...")
    with open(archivo_a_quitar, 'r', encoding='utf-8') as f:
        # Usamos .strip() para limpiar espacios y saltos de línea
        # Esto asegura que "linea1" sea igual a "linea1 " o "linea1\n"
        lineas_a_quitar = {line.strip() for line in f}
    
    print(f"Se cargaron {len(lineas_a_quitar)} líneas únicas para eliminar.")

    # --- 3. Procesar el archivo principal y escribir el resultado ---
    lineas_leidas = 0
    lineas_escritas = 0
    print(f"Procesando '{archivo_principal}'...")

    with open(archivo_principal, 'r', encoding='utf-8') as f_in, \
         open(archivo_salida, 'w', encoding='utf-8') as f_out:
        
        for linea in f_in:
            lineas_leidas += 1
            # Comparamos la versión "limpia" de la línea
            if linea.strip() not in lineas_a_quitar:
                # Si no está, escribimos la línea ORIGINAL (con su salto de línea)
                f_out.write(linea)
                lineas_escritas += 1

    end_time = time.time()
    
    print("\n--- ¡PROCESO COMPLETADO! ---")
    print(f"Archivo de salida guardado como: '{archivo_salida}'")
    print(f"Tiempo total: {end_time - start_time:.2f} segundos")
    print(f"Líneas leídas de '{archivo_principal}': {lineas_leidas}")
    print(f"Líneas eliminadas (repetidas): {lineas_leidas - lineas_escritas}")
    print(f"Líneas guardadas (únicas): {lineas_escritas}")

except FileNotFoundError as e:
    print(f"\nERROR: No se pudo encontrar el archivo: {e.filename}")
    print("Por favor, asegúrate de que el script esté en la misma carpeta que los archivos .txt")
except Exception as e:
    print(f"\nHa ocurrido un error inesperado: {e}")