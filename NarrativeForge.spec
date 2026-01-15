# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
pro_root = os.path.abspath('.')

added_files = [
    (os.path.join(pro_root, 'resources'), 'resources'),
    (os.path.join(pro_root, 'config'), 'config'),
    (os.path.join(pro_root, 'dictionaries'), 'dictionaries'),
    (os.path.join(pro_root, 'styles'), 'styles'),
    (os.path.join(pro_root, 'src', 'sql'), 'src/sql'),
]

added_binaries = [
    (os.path.join(pro_root, 'src\\c_lib\\nf_core_lib.dll'), 'src\\c_lib'), 
]

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=added_binaries,
    datas=added_files,
    hiddenimports=[
        'PySide6.QtXml',
        'reportlab.graphics.barcode.code128',
        'reportlab.graphics.barcode.code39',
        'reportlab.graphics.barcode.code93',
        'reportlab.graphics.barcode.uspc',
        'reportlab.graphics.barcode.usps',
        'reportlab.graphics.barcode.fivefour',
        'reportlab.graphics.barcode.ecc200datamatrix',
        'reportlab.graphics.barcode.usps4s',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NarrativeForge',
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
    icon=[os.path.join(pro_root, 'resources', 'logo.ico')]
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NarrativeForge',
)
