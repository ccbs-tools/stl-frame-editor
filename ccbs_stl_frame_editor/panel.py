"""右上角悬浮面板：绕 X/Y/Z 转 ±90°，撤销 / 复位，另存为 STL。"""

from __future__ import annotations

from PySide6 import QtWidgets

from .gl_widget import StlGLWidget
from .i18n import i18n, tr
from .mesh import AXIS_COLORS


class RotatePanel(QtWidgets.QFrame):
    def __init__(self, gl: StlGLWidget, save_cb):
        super().__init__(gl)
        self.gl = gl
        self.setObjectName("rotPanel")
        self.setStyleSheet("""
            QFrame#rotPanel { background: rgba(20, 22, 28, 190); border: 1px solid rgba(255,255,255,40);
                              border-radius: 8px; }
            QLabel { color: #e6e6e6; background: transparent; }
            QLabel#mat { font-family: Consolas, 'Courier New', monospace; color: #cfd8e3; }
            QPushButton { color: #f0f0f0; background: rgba(255,255,255,28); border: 1px solid rgba(255,255,255,60);
                          border-radius: 4px; padding: 3px 8px; min-width: 52px; }
            QPushButton:hover { background: rgba(255,255,255,55); }
            QPushButton:pressed { background: rgba(255,255,255,90); }
            QPushButton:disabled { color: #888; border-color: rgba(255,255,255,25); }
            QPushButton#save { background: rgba(60, 140, 90, 170); border-color: rgba(120, 220, 150, 120); }
            QPushButton#save:hover { background: rgba(70, 170, 105, 200); }
        """)
        lay = QtWidgets.QGridLayout(self)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setHorizontalSpacing(6)
        lay.setVerticalSpacing(5)

        self.lbl_title = QtWidgets.QLabel()
        self.lbl_title.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_title, 0, 0, 1, 3)

        self.axis_labels: dict[str, QtWidgets.QLabel] = {}
        self.rot_buttons: list[tuple[QtWidgets.QPushButton, str, int]] = []
        for row, axis in enumerate(("X", "Y", "Z"), start=1):
            r, g, b = AXIS_COLORS[axis]
            lab = QtWidgets.QLabel()
            lab.setStyleSheet(f"color: rgb({int(r*255)},{int(g*255)},{int(b*255)}); font-weight: bold;")
            lay.addWidget(lab, row, 0)
            self.axis_labels[axis] = lab
            for col, deg in ((1, 90), (2, -90)):
                btn = QtWidgets.QPushButton(f"{deg:+d}°")
                btn.clicked.connect(lambda _=False, a=axis, d=deg: self.gl.rotate(a, d))
                lay.addWidget(btn, row, col)
                self.rot_buttons.append((btn, axis, deg))

        self.btn_undo = QtWidgets.QPushButton()
        self.btn_undo.clicked.connect(self.gl.undo_rotation)
        self.btn_reset = QtWidgets.QPushButton()
        self.btn_reset.clicked.connect(self.gl.reset_rotation)
        lay.addWidget(self.btn_undo, 4, 1)
        lay.addWidget(self.btn_reset, 4, 2)

        self.lbl_ops = QtWidgets.QLabel()
        self.lbl_ops.setWordWrap(True)
        self.lbl_ops.setMaximumWidth(230)
        lay.addWidget(self.lbl_ops, 5, 0, 1, 3)
        self.lbl_mat = QtWidgets.QLabel("")
        self.lbl_mat.setObjectName("mat")
        lay.addWidget(self.lbl_mat, 6, 0, 1, 3)

        self.btn_save = QtWidgets.QPushButton()
        self.btn_save.setObjectName("save")
        self.btn_save.clicked.connect(save_cb)
        lay.addWidget(self.btn_save, 7, 0, 1, 3)

        gl.rotationChanged.connect(self.refresh)
        gl.resized.connect(self.reposition)
        i18n.languageChanged.connect(self.retranslate)
        self.retranslate()

    def retranslate(self) -> None:
        """按当前语言刷新所有固定文案，再刷新状态文案。"""
        self.lbl_title.setText(tr("panel.title"))
        for axis, lab in self.axis_labels.items():
            lab.setText(tr("panel.axis", axis=axis))
        for btn, axis, deg in self.rot_buttons:
            btn.setToolTip(tr("panel.rotate_tip", axis=axis, deg=f"{deg:+d}"))
        self.btn_undo.setText(tr("panel.undo"))
        self.btn_reset.setText(tr("panel.reset"))
        self.btn_save.setText(tr("panel.save"))
        self.refresh()

    def reposition(self):
        self.adjustSize()
        self.move(self.gl.width() - self.width() - 12, 12)

    def refresh(self):
        has = self.gl.verts is not None
        self.btn_save.setEnabled(has)
        self.btn_undo.setEnabled(has and self.gl.is_rotated)
        self.btn_reset.setEnabled(has and self.gl.is_rotated)
        if not has:
            self.lbl_ops.setText(tr("panel.load_first"))
            self.lbl_mat.setText("")
        elif not self.gl.is_rotated:
            self.lbl_ops.setText(tr("panel.not_rotated"))
            self.lbl_mat.setText("")
        else:
            seq = " → ".join(f"{a}{d:+d}" for a, d in self.gl.ops)
            r, p, y = (int(round(v)) for v in self.gl.rotation_rpy_deg())
            self.lbl_ops.setText(tr("panel.rotated", seq=seq, r=r, p=p, y=y))
            rows = []
            for i, name in enumerate("xyz"):
                vals = " ".join(f"{v:+.0f}".replace("+0", " 0").replace("-0", " 0") for v in self.gl.rot[i])
                rows.append(tr("panel.matrix_row", name=name, vals=vals))
            self.lbl_mat.setText("\n".join(rows))
        self.reposition()
