# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Get the absolute path to the project directory
project_dir = os.path.abspath(os.getcwd())

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/frontend/static', 'app/frontend/static'),
        ('app/frontend/templates', 'app/frontend/templates'),
        ('run.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'pandas',
        'numpy',
        'scipy',
        'sklearn',
        'matplotlib',
        'seaborn',
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'PyQt5.QtCore',
        'requests',
        'urllib3',
    ],
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
    name='IntelligentBiostats',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 