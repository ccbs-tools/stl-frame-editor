# -*- mode: python ; coding: utf-8 -*-
# 文件夹打包（启动快）：uv run pyinstaller main.spec --noconfirm  →  dist/stl-frame-editor/stl-frame-editor.exe

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/icon.ico', 'assets'), ('assets/icon.png', 'assets')],   # 运行时图标（make_app_icon 从 _MEIPASS/assets 找）
    hiddenimports=['stl_frame_editor'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineQuick',
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.Qt3DCore', 'PySide6.Qt3DRender',
        'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtSensors',
        'PySide6.QtSerialPort', 'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtXml',
        'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtUiTools',
        'tkinter', 'matplotlib', 'IPython', 'pytest',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='stl-frame-editor',
    icon='assets/icon.ico',
    contents_directory='stl-frame-editor-lib',   # 依赖目录名（PyInstaller 6 默认 _internal）
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,   # Qt DLL 压缩后易出问题
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
    a.datas,
    name='stl-frame-editor',
    strip=False,
    upx=False,
    upx_exclude=[],
)
