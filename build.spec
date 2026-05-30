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
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtMultimedia',
    'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtBluetooth',
    'PyQt5.QtDesigner',
    'PyQt5.QtHelp',
    'PyQt5.QtLocation',
    'PyQt5.QtNfc',
    'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtRemoteObjects',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtSql',
    'PyQt5.QtSvg',
    'PyQt5.QtTest',
    'PyQt5.QtTextToSpeech',
    'PyQt5.QtWebChannel',
    'PyQt5.QtWebSockets',
    'PyQt5.QtXml',
    'PyQt5.QtXmlPatterns',
    'PyQt5.QtDBus',
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
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
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

# Remove unnecessary Qt plugins that add to size
import os
plugins_to_keep = {'platforms', 'styles', 'imageformats'}
a.binaries = [
    b for b in a.binaries
    if not (
        'QtWebEngine' in b[0] or
        'Qt5WebEngine' in b[0] or
        'Qt5Multimedia' in b[0] or
        'Qt5Quick' in b[0] or
        'Qt5Qml' in b[0] or
        'Qt5Svg' in b[0] or
        'Qt5Network' in b[0] or
        'opengl32sw' in b[0] or
        'd3dcompiler' in b[0] or
        'libGLESv2' in b[0] or
        'libEGL' in b[0]
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
