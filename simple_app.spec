# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect MNE modules
mne_hiddenimports = collect_submodules('mne')
mne_datas = collect_data_files('mne')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=mne_datas,
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'numpy',
        'scipy',
        'pandas',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'lazy_loader',
        'lazy_loader.lazy_loader',
        'serial',
        'serial.tools.list_ports',
    ] + mne_hiddenimports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'ipykernel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EEG_Analysis',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EEG_Analysis'
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='EEG_Analysis.app',
        icon=None,
        bundle_identifier='com.eeganalysis.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
        }
    )
