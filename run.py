# run.py (versión final con apertura de navegador)
import sys
import os
import webbrowser  # <-- 1. IMPORTAMOS EL MÓDULO
from streamlit.web.cli import main as stcli

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    dashboard_path = resource_path("franjas_dashboard.py")
    
    # 2. DEFINIMOS LA URL QUE VAMOS A ABRIR
    url = "http://localhost:8501"
    
    args = [
        "run",
        dashboard_path,
        f"--server.port=8501",
        "--server.headless=true",
        "--global.developmentMode=false",
    ]
    
    # 3. ABRIMOS EL NAVEGADOR
    webbrowser.open(url)
    
    sys.argv = ["streamlit"] + args
    sys.exit(stcli())

if __name__ == "__main__":
    main()