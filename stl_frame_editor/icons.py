"""应用图标：优先加载 assets/icon.ico（源码运行取项目根目录，打包后取 _MEIPASS），找不到就现画一个。"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui


def assets_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "assets"
    return Path(__file__).resolve().parents[1] / "assets"


def draw_icon_pixmap(size: int) -> QtGui.QPixmap:
    """回退图标：深色圆角方块 + XYZ 三色轴。正式图标在 assets/icon.ico。"""
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
    return pm


def app_icon() -> QtGui.QIcon:
    for name in ("icon.ico", "icon.png"):
        path = assets_dir() / name
        if path.is_file():
            return QtGui.QIcon(str(path))
    icon = QtGui.QIcon()
    for size in (16, 32, 48, 64, 128, 256):
        icon.addPixmap(draw_icon_pixmap(size))
    return icon


__all__ = ["app_icon", "assets_dir"]
