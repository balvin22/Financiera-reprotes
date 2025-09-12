# run.py
import sys
import os
import webbrowser
from streamlit.web import bootstrap

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def run_streamlit():
    # La ruta a tu script principal de Streamlit, usando resource_path
    script_path = resource_path("franjas_dashboard.py")
    
    # Prepara los argumentos para Streamlit
    args = [
        "--server.headless", "true",
        "--server.port", "8501",
        "--server.runOnSave", "false",
        "--browser.serverAddress", "localhost"
    ]
    
    # Abrir el navegador justo cuando el servidor esté listo (opcional pero mejora la experiencia)
    webbrowser.open("http://localhost:8501")
    
    # Llama directamente a la función de arranque de Streamlit
    bootstrap.run(script_path, "run", args, flag_options={})

if __name__ == "__main__":
    run_streamlit()