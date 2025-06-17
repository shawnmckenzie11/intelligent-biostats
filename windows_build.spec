# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['windows_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('run.py', '.'),
        ('startup.py', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'pandas',
        'numpy',
        'scipy',
        'matplotlib',
        'seaborn',
        'sqlalchemy',
        'werkzeug',
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/frontend/static/img/icon.ico'
) 