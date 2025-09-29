import subprocess
import os
import sys
import shutil

def get_script_path():
    """ Devuelve la ruta al script principal del dashboard. """
    relative_path = os.path.join('src', 'views', 'graficos', 'base_dashboard', 'main.py')
    
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    streamlit_path = shutil.which('streamlit')

    if streamlit_path is None:
        print("Error: No se pudo encontrar el ejecutable de 'streamlit'.")
        sys.exit(1)

    script_to_run = get_script_path()

    # --- CAMBIO CLAVE: Quitamos el modo headless ---
    command = [
        streamlit_path,
        "run",
        script_to_run,
        "--server.port=8501" # Mantenemos el puerto por si acaso
        # La línea "--server.headless=true" ha sido eliminada.
    ]
    
    try:
        subprocess.run(command)
    except Exception as e:
        print(f"Ocurrió un error al intentar ejecutar Streamlit: {e}")
        input("Presiona Enter para salir...")