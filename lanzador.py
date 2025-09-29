import sys
import os
import multiprocessing
import time
import webbrowser
import tkinter as tk
from streamlit.web import cli as stcli

def run_streamlit():
    """Prepara los argumentos y llama a la función principal de Streamlit."""
    script_path = get_resource_path(os.path.join('src', 'views', 'graficos', 'base_dashboard', 'main.py'))
    
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--server.port=8501",
        "--global.developmentMode=false",
        "--server.headless=true",
    ]
    
    stcli.main()

def get_resource_path(relative_path):
    """ Obtiene la ruta al recurso, funcionando para desarrollo y para el .exe de PyInstaller. """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    # Es necesario para que multiprocessing funcione correctamente al ser empaquetado.
    multiprocessing.freeze_support()

    # 1. Creamos un PROCESO para el servidor de Streamlit.
    streamlit_process = multiprocessing.Process(target=run_streamlit, daemon=True)
    
    # 2. Iniciamos el proceso.
    streamlit_process.start()
    
    time.sleep(4) # Damos un poco más de tiempo al proceso para que inicie.
    webbrowser.open("http://localhost:8501")
    
    # --- Lógica de la ventana (casi igual) ---
    root = tk.Tk()
    root.title("Control del Dashboard")
    root.geometry("350x150")
    root.eval('tk::PlaceWindow . center')
    
    label = tk.Label(root, text="\nEl servidor del dashboard está activo.\n\nCierre esta ventana para detenerlo.", font=("Helvetica", 10))
    label.pack(pady=20)
    
    # 3. La función de cierre ahora termina el PROCESO.
    def on_closing():
        print("Cerrando la ventana, terminando el proceso del servidor...")
        streamlit_process.terminate() # Envía la señal para terminar el proceso.
        root.destroy() # Cierra la ventana.

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()