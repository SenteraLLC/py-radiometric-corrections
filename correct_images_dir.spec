# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['scripts\\correct_images.py'],
    pathex=['.'],
    binaries=[],
    datas=[('exiftool/exiftool.exe', '.')],
    hiddenimports=['pkg_resources.py2_warn'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ImageryCorrector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ImageryCorrector',
)
