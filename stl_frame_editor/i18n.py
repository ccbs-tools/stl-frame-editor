"""界面文案的中英文切换。

用法：
    from .i18n import tr, i18n
    label.setText(tr("panel.undo"))
    i18n.languageChanged.connect(self.retranslate)

语言保存在 QSettings（组织 CCBS / 程序 CCBS STL View），首次运行默认英文。
"""

from __future__ import annotations

from PySide6 import QtCore

DEFAULT_LANG = "en"
LANGUAGES = (("en", "English"), ("zh", "中文（简体）"))
_SETTINGS_KEY = "language"

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "app.title": "STL Coordinate Frame Editor",
        "menu.file": "&File",
        "menu.open": "&Open...",
        "menu.save_as": "Save &As STL...",
        "menu.fit": "&Fit View",
        "menu.quit": "&Quit",
        "menu.language": "&Language",
        "status.drop_hint": "Drop a .stl file into the window",
        "status.no_mesh": "No STL loaded yet",
        "dialog.open_title": "Open STL",
        "dialog.open_filter": "STL files (*.stl *.STL);;All files (*)",
        "dialog.save_title": "Save As STL",
        "dialog.save_filter": "STL files (*.stl *.STL)",
        "dialog.overwrite_title": "Overwrite original file?",
        "dialog.overwrite_text": "This will overwrite the currently open file:\n{path}\n\nContinue?",
        "panel.title": "Rotate model (world axes, about origin)",
        "panel.axis": "{axis} axis",
        "panel.rotate_tip": "Rotate {deg}° about the {axis} axis (right-hand rule)",
        "panel.undo": "Undo",
        "panel.reset": "Reset",
        "panel.not_rotated": "Not rotated",
        "panel.load_first": "Load an STL first",
        "panel.rotated": "Rotated: {seq}\nEquivalent rpy = ({r}°, {p}°, {y}°)",
        "panel.matrix_row": "new {name} = [{vals}]·orig",
        "panel.save": "Save As STL…",
        "gl.load_failed": "Failed to load {name}: {err}",
        "gl.no_triangles": "{name} has no triangles",
        "gl.save_failed": "Failed to save {name}: {err}",
        "gl.saved": "Saved {path}    ({n} triangles)",
        "gl.unit_mm": "size > 5, looks like mm",
        "gl.unit_m": "size ≤ 5, looks like m",
        "gl.rotated_note": "    [rotated, unsaved]",
        "gl.mesh_info": "{name}{note}    triangles {n}    bbox min({mn})  max({mx})  size {ext}    {unit}",
        "gl.drop_here": "Drop a .stl file here\n\n(or Ctrl+O to open)",
        "gl.tips": "LMB rotate  RMB/MMB pan  Wheel zoom    F fit  R reset  W wireframe  G grid  A axes    grid step {step}",
    },
    "zh": {
        "app.title": "STL 坐标系修改器",
        "menu.file": "文件(&F)",
        "menu.open": "打开(&O)...",
        "menu.save_as": "另存为 STL(&A)...",
        "menu.fit": "适配视角(&F)",
        "menu.quit": "退出(&Q)",
        "menu.language": "语言(&L)",
        "status.drop_hint": "把 .stl 文件拖进窗口",
        "status.no_mesh": "还没有加载 STL",
        "dialog.open_title": "打开 STL",
        "dialog.open_filter": "STL 文件 (*.stl *.STL);;所有文件 (*)",
        "dialog.save_title": "另存为 STL",
        "dialog.save_filter": "STL 文件 (*.stl *.STL)",
        "dialog.overwrite_title": "覆盖原文件？",
        "dialog.overwrite_text": "将覆盖当前打开的文件：\n{path}\n\n确定吗？",
        "panel.title": "模型旋转（绕世界轴、绕原点）",
        "panel.axis": "{axis} 轴",
        "panel.rotate_tip": "绕 {axis} 轴转 {deg}°（右手定则）",
        "panel.undo": "撤销",
        "panel.reset": "复位",
        "panel.not_rotated": "未旋转",
        "panel.load_first": "先加载一个 STL",
        "panel.rotated": "已旋转: {seq}\n等效 rpy = ({r}°, {p}°, {y}°)",
        "panel.matrix_row": "新{name} = [{vals}]·原",
        "panel.save": "另存为 STL…",
        "gl.load_failed": "加载失败 {name}: {err}",
        "gl.no_triangles": "{name} 里没有三角面",
        "gl.save_failed": "保存失败 {name}: {err}",
        "gl.saved": "已保存 {path}    ({n} 三角面)",
        "gl.unit_mm": "尺寸 > 5，像是 mm 单位",
        "gl.unit_m": "尺寸 ≤ 5，像是 m 单位",
        "gl.rotated_note": "    [已旋转，未保存]",
        "gl.mesh_info": "{name}{note}    三角面 {n}    包围盒 min({mn})  max({mx})  尺寸 {ext}    {unit}",
        "gl.drop_here": "把 .stl 文件拖到这里\n\n（或 Ctrl+O 打开）",
        "gl.tips": "左键旋转  右键/中键平移  滚轮缩放    F 适配  R 复位  W 线框  G 网格  A 坐标轴    网格间距 {step}",
    },
}


class _I18n(QtCore.QObject):
    languageChanged = QtCore.Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._lang = DEFAULT_LANG

    @property
    def lang(self) -> str:
        return self._lang

    def load(self) -> str:
        """从 QSettings 读取上次选择的语言；需在 QApplication 创建后调用。"""
        saved = QtCore.QSettings().value(_SETTINGS_KEY, DEFAULT_LANG)
        self._lang = saved if saved in _STRINGS else DEFAULT_LANG
        return self._lang

    def set(self, lang: str) -> None:
        if lang not in _STRINGS or lang == self._lang:
            return
        self._lang = lang
        QtCore.QSettings().setValue(_SETTINGS_KEY, lang)
        self.languageChanged.emit(lang)

    def tr(self, key: str, **kwargs) -> str:
        table = _STRINGS.get(self._lang, {})
        text = table.get(key) or _STRINGS[DEFAULT_LANG].get(key) or key
        return text.format(**kwargs) if kwargs else text


i18n = _I18n()


def tr(key: str, **kwargs) -> str:
    return i18n.tr(key, **kwargs)
