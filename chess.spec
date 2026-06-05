# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec dosyası - Satranç Uygulaması
"""

import os
import sys

block_cipher = None

# Proje dizini
project_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ('stockfish/stockfish-windows-x86-64-avx2.exe', 'stockfish'),
        ('themes', 'themes'),
        ('logo.ico', '.'),
    ],
    hiddenimports=[
        'chess',
        'chess.pgn',
        'chess.engine',
        'customtkinter',
        'PIL',
        'PIL.Image',
        'requests',
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
    name='Satranc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI uygulaması, konsol yok
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',  # Uygulama ikonu
)
