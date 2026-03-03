# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path.cwd()

hidden_imports = collect_submodules("apidev")
# Typer/Click rely on dynamic imports in some environments.
hidden_imports += collect_submodules("typer")
hidden_imports += collect_submodules("click")
# Rich resolves unicode tables via dynamic import names.
hidden_imports += collect_submodules("rich._unicode_data")


# Package data required at runtime (e.g. init_service reads templates via importlib.resources).
templates_src = project_root / "src" / "apidev" / "templates"
datas = [(str(templates_src), "apidev/templates")] if templates_src.is_dir() else []

a = Analysis(
    [str(project_root / "src" / "apidev" / "cli.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="apidev",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="apidev",
)
