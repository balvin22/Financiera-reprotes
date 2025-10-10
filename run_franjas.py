import sys
import os
import multiprocessing
import time
import webbrowser
import tkinter as tk
from streamlit.web import cli as stcli

def get_resource_path(relative_path):
    """ 
    Obtiene la ruta absoluta al recurso. Funciona tanto en desarrollo 
    como cuando está empaquetado con PyInstaller.
    """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

def run_streamlit():
    """Prepara los argumentos y llama a la función principal de Streamlit."""
    
    # --- ¡ESTA ES LA LÍNEA MÁS IMPORTANTE! ---
    # Le decimos al lanzador que el script a ejecutar es 'dashboard_app.py'
    script_path = get_resource_path('franjas_dashboard.py')
    
    # Argumentos para correr Streamlit de forma controlada
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--server.port=8501",          # Usar un puerto fijo
        "--global.developmentMode=false", # Desactivar modo desarrollo
        "--server.headless=true",      # No abrir una nueva ventana de navegador automáticamente (lo haremos nosotros)
    ]
    
    # Llama a la función principal de Streamlit para iniciar el servidor
    stcli.main()

if __name__ == "__main__":
    # Necesario para que multiprocessing funcione correctamente en el .exe
    multiprocessing.freeze_support()

    # 1. Creamos un proceso separado para el servidor de Streamlit.
    #    'daemon=True' asegura que el proceso se cierre si el script principal termina.
    streamlit_process = multiprocessing.Process(target=run_streamlit, daemon=True)
    
    # 2. Iniciamos el proceso del servidor.
    streamlit_process.start()
    
    # 3. Damos un par de segundos al servidor para que arranque completamente.
    time.sleep(5) 
    
    # 4. Abrimos el navegador web apuntando a la dirección del servidor.
    webbrowser.open("http://localhost:8501")
    
    # 5. Creamos una pequeña ventana con Tkinter para mantener el programa activo.
    root = tk.Tk()
    root.title("Control del Dashboard")
    root.geometry("350x150")
    # Centrar la ventana
    root.eval('tk::PlaceWindow . center')
    
    label = tk.Label(root, text="\nEl servidor del dashboard está activo.\n\nCierre esta ventana para detenerlo.", font=("Helvetica", 10))
    label.pack(pady=20)
    
    # 6. Definimos qué hacer cuando se cierra la ventana.
    def on_closing():
        print("Cerrando la ventana, terminando el proceso del servidor...")
        streamlit_process.terminate() # Envía la señal para terminar el proceso de Streamlit.
        root.destroy()                # Cierra la ventana de Tkinter.

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Mantiene la ventana de Tkinter visible y el programa en ejecución.
    root.mainloop()