# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# --- INICIO DE LA CONFIGURACIÓN IMPORTANTE ---

# Recolectar todos los archivos necesarios para Streamlit y Plotly
datas = []
datas += collect_data_files("streamlit")
datas += collect_data_files("plotly")

# Lista de librerías que PyInstaller a menudo no encuentra (importaciones ocultas)
hiddenimports = [
    "streamlit",
    "plotly.graph_objects",
    "plotly.express",
    "pandas",
    "numpy",
    "pyarrow",
    "watchdog"
]

# --- FIN DE LA CONFIGURACIÓN IMPORTANTE ---

a = Analysis(
    ['franjas_dashboard.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DashboardFinanciero',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # <-- console=False es lo mismo que --windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)