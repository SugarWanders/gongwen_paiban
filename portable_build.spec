# -*- mode: python ; coding: utf-8 -*-


app_name = "公文排版助手V1_3_2"


a = Analysis(
    ["app/main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("icon.png", "."),
        ("icon.ico", "."),
        ("app/ui/assets/down-arrow.svg", "app/ui/assets"),
        ("app/ui/assets/checkmark.svg", "app/ui/assets"),
        ("app/ui/assets/up-arrow.svg", "app/ui/assets"),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
