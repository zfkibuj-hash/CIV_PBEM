# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Civ4 PBEM Manager.
Build with: pyinstaller build.spec

Size optimization tips:
- excludes: removes unused Qt modules (QtWebEngine, QtMultimedia, etc.)
- upx=True: compresses binaries (install UPX: https://github.com/upx/upx/releases)
- strip=True: removes debug symbols (Linux/Mac, no effect on Windows)
- For even smaller builds, use --onedir instead of --onefile (avoids repacking)
"""

block_cipher = None

# Modules we don't use - excluding them saves 10-20MB
EXCLUDES = [
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtBluetooth',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtLocation',
    'PySide6.QtNfc',
    'PySide6.QtOpenGL',
    'PySide6.QtPositioning',
    'PySide6.QtPrintSupport',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtSql',
    'PySide6.QtSvg',
    'PySide6.QtTest',
    'PySide6.QtTextToSpeech',
    'PySide6.QtWebChannel',
    'PySide6.QtWebSockets',
    'PySide6.QtXml',
    'PySide6.QtDBus',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DRender',
    'PySide6.Qt3DInput',
    'PySide6.QtDataVisualization',
    'PySide6.QtCharts',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    'PySide6.QtShaderTools',
    'PySide6.QtVirtualKeyboard',
    'PySide6.QtSpatialAudio',
    'PySide6.QtScxml',
    'PySide6.QtStateMachine',
    'PySide6.QtHttpServer',
    'PySide6.QtNetworkAuth',
    # chardet (pulled by email parsing but huge)
    'chardet',
    'charset_normalizer',
    # Unused stdlib modules
    'tkinter',
    'unittest',
    'pydoc',
    'doctest',
    'xmlrpc',
    'lib2to3',
    'test',
    'distutils',
    'setuptools',
    'pkg_resources',
    'numpy',
    'PIL',  # only needed for generate_icon.py, not runtime
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.')],
    hiddenimports=[
        'paramiko',
        'PySide6',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary Qt plugins and DLLs that add to size
import os
plugins_to_keep = {'platforms', 'styles', 'imageformats'}
a.binaries = [
    b for b in a.binaries
    if not (
        'QtWebEngine' in b[0] or
        'Qt6WebEngine' in b[0] or
        'Qt6Multimedia' in b[0] or
        'Qt6Quick' in b[0] or
        'Qt6Qml' in b[0] or
        'Qt6Svg' in b[0] or
        'Qt6Network' in b[0] or
        'Qt6Pdf' in b[0] or
        'Qt6OpenGL' in b[0] or
        'Qt6QmlModels' in b[0] or
        'Qt6VirtualKeyboard' in b[0] or
        'Qt6Positioning' in b[0] or
        'Qt6ShaderTools' in b[0] or
        'opengl32sw' in b[0] or
        'd3dcompiler' in b[0] or
        'libGLESv2' in b[0] or
        'libEGL' in b[0] or
        'QtQuick' in b[0] or
        'QtQml' in b[0] or
        'QtOpenGL' in b[0] or
        'QtPdf' in b[0] or
        'QtNetwork' in b[0] or
        'QtSvg' in b[0]
    )
]

# Also strip from datas
a.datas = [
    d for d in a.datas
    if not (
        'translations' in d[0].lower() or
        'QtWebEngine' in d[0] or
        'qml' in d[0].lower()
    )
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Civ4PBEMManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
