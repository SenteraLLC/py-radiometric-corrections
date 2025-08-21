# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['scripts\\correct_images_gui.py'],
             pathex=['.'],
             binaries=[],
             datas=[('exiftool/exiftool.exe', '.'), ('cfg/exiftool.cfg', 'cfg'), ('cfg/reg_config.ini', 'cfg')],
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
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ImageryCorrectorGUI',
          icon='corrections_gui_icon.ico'
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
