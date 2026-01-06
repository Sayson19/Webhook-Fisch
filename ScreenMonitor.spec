# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['screen_monitor.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\kolod\\AppData\\Local\\Programs\\Python\\Python*\\Lib\\site-packages\\customtkinter', 'customtkinter')],
    hiddenimports=['PIL', 'PIL.Image', 'PIL.ImageGrab', 'numpy', 'customtkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ScreenMonitor',
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
    icon='NONE',
)
