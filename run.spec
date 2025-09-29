# run.spec (versión final con hiddenimport de CLI)
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# --- CONFIGURACIÓN CLAVE ---
streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all('streamlit')
streamlit_hiddenimports.append('watchdog')

# --- FORZAR LA INCLUSIÓN DE METADATOS ---
streamlit_metadata_path = 'C:\\Users\\sb118\\Desktop\\Financiera-reprotes\\entorno_estable\\Lib\\site-packages\\streamlit-1.49.1.dist-info'
# --- FIN DE LA CONFIGURACIÓN ---

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=streamlit_binaries,
    datas=streamlit_datas + [
        ('franjas_dashboard.py', '.'),
        (streamlit_metadata_path, 'Lib/site-packages/streamlit-1.49.1.dist-info')
    ],
    # AÑADIMOS MANUALMENTE EL MÓDULO 'cli' QUE FALTABA
    hiddenimports=streamlit_hiddenimports + ['streamlit.cli'],
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
    [],
    exclude_binaries=True,
    name='run',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='run'
)