# find_path.py
import os
from importlib.metadata import distribution

try:
    # Obtiene la información del paquete 'streamlit'
    dist = distribution('streamlit')

    # Encuentra la ruta de la carpeta de metadatos (ej: streamlit-1.49.1.dist-info)
    # Buscamos un archivo conocido dentro de esa carpeta y obtenemos la ruta de su directorio padre.
    metadata_file = next(f for f in dist.files if 'METADATA' in str(f))
    metadata_path = str(metadata_file.locate().parent)

    print("\n--- ¡Ruta de metadatos encontrada! ---")
    print(f"Ruta completa: {metadata_path}")

    # Obtenemos solo el nombre de la carpeta para el comando de PyInstaller
    folder_name = os.path.basename(metadata_path)

    # Construimos el argumento exacto que necesitas
    pyinstaller_arg = f'--add-data "{metadata_path}{os.pathsep}{folder_name}"'

    print("\n✅ Copia el siguiente argumento y pégalo en tu comando de PyInstaller:")
    print(pyinstaller_arg)
    print("-" * 35)

except Exception as e:
    print(f"Error: No se pudo encontrar la ruta de metadatos para Streamlit. {e}")