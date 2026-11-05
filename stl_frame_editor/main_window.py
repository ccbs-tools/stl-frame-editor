"""主窗口与应用图标。"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .changelog import REPO_HOME, VIDEO_TUTORIAL
from .gl_widget import StlGLWidget
from .i18n import LANGUAGES, i18n, tr
from .log import logger
from .panel import RotatePanel
from .version_dialogs import ChangelogDialog, UpdateCheckDialog


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, initial: str | None = None):
        super().__init__()
        self.resize(1100, 760)
        self.setAcceptDrops(True)

        self.gl = StlGLWidget(self)
        self.setCentralWidget(self.gl)
        self.gl.meshLoaded.connect(self._on_loaded)
        self.gl.loadFailed.connect(lambda msg: self.statusBar().showMessage(msg, 8000))
        self.panel = RotatePanel(self.gl, self.save_dialog)

        self.act_open = QtGui.QAction(self)
        self.act_open.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self.open_dialog)
        self.act_save = QtGui.QAction(self)
        self.act_save.setShortcut(QtGui.QKeySequence.StandardKey.SaveAs)
        self.act_save.triggered.connect(self.save_dialog)
        self.act_fit = QtGui.QAction(self)
        self.act_fit.triggered.connect(self.gl.fit_view)
        self.act_quit = QtGui.QAction(self)
        self.act_quit.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        self.act_quit.triggered.connect(self.close)
        self.menu_file = self.menuBar().addMenu("")
        self.menu_file.addAction(self.act_open)
        self.menu_file.addAction(self.act_save)
        self.menu_file.addAction(self.act_fit)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_quit)

        # 语言菜单：各语言用自己的名字显示，不随当前语言翻译
        self.menu_lang = self.menuBar().addMenu("")
        self.lang_group = QtGui.QActionGroup(self)
        self.lang_group.setExclusive(True)
        for code, label in LANGUAGES:
            act = QtGui.QAction(label, self, checkable=True)
            act.setData(code)
            act.setChecked(code == i18n.lang)
            act.triggered.connect(lambda _=False, c=code: i18n.set(c))
            self.lang_group.addAction(act)
            self.menu_lang.addAction(act)

        self.menu_help = self.menuBar().addMenu("")
        self.act_repo = QtGui.QAction(self)
        self.act_repo.triggered.connect(lambda: self._open_url(REPO_HOME))
        self.act_video = QtGui.QAction(self)
        self.act_video.triggered.connect(lambda: self._open_url(VIDEO_TUTORIAL))
        self.act_changelog = QtGui.QAction(self)
        self.act_changelog.triggered.connect(self._show_changelog)
        self.act_check_update = QtGui.QAction(self)
        self.act_check_update.triggered.connect(self._show_update_check)
        self.menu_help.addAction(self.act_repo)
        self.menu_help.addAction(self.act_video)
        self.menu_help.addSeparator()
        self.menu_help.addAction(self.act_changelog)
        self.menu_help.addAction(self.act_check_update)

        i18n.languageChanged.connect(self.retranslate)
        self.retranslate()

        if initial:
            QtCore.QTimer.singleShot(0, lambda: self.gl.load(initial))

    def retranslate(self) -> None:
        self.menu_file.setTitle(tr("menu.file"))
        self.act_open.setText(tr("menu.open"))
        self.act_save.setText(tr("menu.save_as"))
        self.act_fit.setText(tr("menu.fit"))
        self.act_quit.setText(tr("menu.quit"))
        self.menu_lang.setTitle(tr("menu.language"))
        for act in self.lang_group.actions():
            act.setChecked(act.data() == i18n.lang)
        self.menu_help.setTitle(tr("menu.help"))
        self.act_repo.setText(tr("menu.repo"))
        self.act_video.setText(tr("menu.video"))
        self.act_changelog.setText(tr("menu.changelog"))
        self.act_check_update.setText(tr("menu.check_update"))
        self._update_title()
        if self.gl.verts is None:
            self.statusBar().showMessage(tr("status.drop_hint"))
        # 已加载时 gl.retranslate 会重新发 meshLoaded，状态栏随之更新

    @staticmethod
    def _open_url(url: str) -> None:
        ok = QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        logger.info("打开链接: {} -> {}", url, "ok" if ok else "失败")

    def _show_changelog(self) -> None:
        logger.info("打开「版本介绍」")
        ChangelogDialog(self).exec()

    def _show_update_check(self) -> None:
        logger.info("菜单触发「检查更新」")
        UpdateCheckDialog(self).exec()

    def _update_title(self) -> None:
        if self.gl.path is None:
            self.setWindowTitle(tr("app.title"))
        else:
            mark = " *" if self.gl.is_rotated else ""
            self.setWindowTitle(f"{tr('app.title')} — {self.gl.path.name}{mark}")

    def _on_loaded(self, info: str):
        self.statusBar().showMessage(info)
        self._update_title()

    def open_dialog(self):
        start = str(self.gl.path.parent) if self.gl.path else ""
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, tr("dialog.open_title"), start, tr("dialog.open_filter"))
        if fn:
            logger.info("打开对话框选择: {}", fn)
            self.gl.load(fn)
        else:
            logger.debug("打开对话框取消")

    def save_dialog(self):
        if self.gl.mesh is None:
            logger.debug("另存为：尚未加载 STL，忽略")
            self.statusBar().showMessage(tr("status.no_mesh"), 4000)
            return
        src = self.gl.path
        suffix = "_" + "".join(f"{a}{'p' if d > 0 else 'n'}{abs(d)}" for a, d in self.gl.ops) if self.gl.ops else ""
        default = src.with_name(f"{src.stem}{suffix or '_copy'}{src.suffix}")
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, tr("dialog.save_title"), str(default), tr("dialog.save_filter"))
        if not fn:
            logger.debug("另存为对话框取消")
            return
        if not fn.lower().endswith(".stl"):
            fn += ".stl"
        if Path(fn).resolve() == src.resolve():
            logger.warning("另存为目标与源文件相同，询问是否覆盖: {}", src)
            ret = QtWidgets.QMessageBox.question(
                self, tr("dialog.overwrite_title"), tr("dialog.overwrite_text", path=src),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No)
            if ret != QtWidgets.QMessageBox.StandardButton.Yes:
                logger.info("用户取消覆盖原文件")
                return
            logger.info("用户确认覆盖原文件")
        self.gl.save_as(fn)

    # 整个窗口（含菜单栏、状态栏）都接受拖放，转交给 GL 控件
    def dragEnterEvent(self, e):
        self.gl.dragEnterEvent(e)

    def dropEvent(self, e):
        self.gl.dropEvent(e)


def _icon_search_dirs() -> list[Path]:
    dirs: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        dirs.append(Path(meipass))
    pkg = Path(__file__).resolve().parent
    dirs.append(pkg)            # 包内
    dirs.append(pkg.parent)     # 项目根目录（源码运行时 icon 在这里）
    exe_dir = Path(sys.executable).resolve().parent
    dirs.append(exe_dir)
    return dirs


def make_app_icon() -> QtGui.QIcon:
    """程序图标：优先用 icon.ico / icon.png，否则画一个 XYZ 三色轴图标。"""
    for d in _icon_search_dirs():
        for name in ("icon.ico", "icon.png"):
            p = d / name
            if p.is_file():
                return QtGui.QIcon(str(p))

    icon = QtGui.QIcon()
    for size in (16, 32, 48, 64, 128, 256):
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        r = size * 0.12
        p.setBrush(QtGui.QColor(28, 32, 40))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, size, size, r, r)
        o = QtCore.QPointF(size * 0.42, size * 0.58)
        L = size * 0.32
        pen = QtGui.QPen()
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setWidthF(max(1.5, size * 0.08))
        for color, dx, dy in (
            (QtGui.QColor(235, 50, 50), L, L * 0.15),
            (QtGui.QColor(50, 200, 50), -L * 0.15, -L),
            (QtGui.QColor(60, 110, 255), L * 0.55, -L * 0.55),
        ):
            pen.setColor(color)
            p.setPen(pen)
            p.drawLine(o, QtCore.QPointF(o.x() + dx, o.y() + dy))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QColor(255, 255, 255))
        p.drawEllipse(o, size * 0.05, size * 0.05)
        p.end()
        icon.addPixmap(pm)
    return icon
