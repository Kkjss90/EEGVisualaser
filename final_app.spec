# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # PyQt5
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',

        # MNE - расширенные импорты
        'mne',
        'mne.io',
        'mne.io.edf',
        'mne.io.eeglab',
        'mne.viz',
        'mne.epochs',
        'mne.preprocessing',
        'mne.channels',
        'mne.stats',
        'mne.time_frequency',
        'mne.connectivity',
        'mne.decoding',
        'mne.filter',
        'mne.utils',
        'mne.datasets',
        'mne.datasets.utils',
        'lazy_loader',
        'lazy_loader.lazy_loader',

        # NumPy
        'numpy',
        'numpy.core',
        'numpy.core.multiarray',
        'numpy.core.umath',
        'numpy.lib',
        'numpy.linalg',
        'numpy.fft',
        'numpy.random',

        # SciPy
        'scipy',
        'scipy.signal',
        'scipy.signal.windows',
        'scipy.signal.filter_design',
        'scipy.stats',
        'scipy.ndimage',
        'scipy.sparse',
        'scipy.optimize',
        'scipy.integrate',
        'scipy.interpolate',
        'scipy.special',
        'scipy.io',

        # Pandas
        'pandas',
        'pandas.io',
        'pandas.core',
        'pandas._libs',
        'pandas._libs.tslibs',

        # Matplotlib
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.figure',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_agg',
        'matplotlib.backend_bases',
        'matplotlib.cm',
        'matplotlib.colors',
        'matplotlib.patches',
        'matplotlib.text',
        'matplotlib.font_manager',
        'matplotlib.image',
        'matplotlib.lines',
        'matplotlib.axes',
        'matplotlib.axis',
        'matplotlib.ticker',
        'matplotlib.transforms',
        'matplotlib.collections',

        # Scikit-learn
        'sklearn',
        'sklearn.base',
        'sklearn.utils',
        'sklearn.preprocessing',
        'sklearn.metrics',

        # Другие
        'pathlib',
        'warnings',
        'threading',
        'multiprocessing',
        'functools',
        'itertools',
        'collections',
        'copy',
        'typing',

        # Lazy loader for MNE
        'lazy_loader',
        'lazy_loader.lazy_loader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        # Исключаем конфликтующие модули
        'tkinter',
        'tkinter.ttk',
        'IPython',
        'jupyter',
        'notebook',
        'ipykernel',
        'ipywidgets',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_gtk3agg',
        'matplotlib.backends.backend_gtk3cairo',
        'matplotlib.backends.backend_webagg',
        'matplotlib.backends.backend_nbagg',
        'matplotlib.backends.backend_svg',
        'matplotlib.backends.backend_pdf',
        'matplotlib.backends.backend_ps',
        'matplotlib.backends.backend_template',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EEG_Analysis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Не показывать консоль
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# Для macOS создаем .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='EEG_Analysis.app',
        icon=None,
        bundle_identifier='com.eeganalysis.final.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'NSHumanReadableCopyright': 'Приложение для анализа ЭЭГ',
            'LSMinimumSystemVersion': '10.12.0',
            'NSAppTransportSecurity': {
                'NSAllowsArbitraryLoads': True,
            },
            'CFBundleIdentifier': 'com.eeganalysis.final.app',
            'CFBundleDisplayName': 'Анализ ЭЭГ',
            'CFBundleName': 'EEG Analysis',
            'CFBundleVersion': '1.0.0',
            'CFBundleExecutable': 'EEG_Analysis',
            'NSRequiresAquaSystemAppearance': False,
        },
    )
