"""OpenGL 视口：显示 STL、原点 XYZ 轴、地面网格；转台相机；拖放加载。"""

from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np
import trimesh
from OpenGL import GL, GLU
from PySide6 import QtCore, QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from .i18n import i18n, tr
from .log import logger
from .mesh import AXIS_COLORS, AXIS_DIRS, load_stl, rot_matrix, rotation_rpy_deg

MESH_COLOR = (0.72, 0.76, 0.80)
BG_TOP = (0.18, 0.20, 0.24)
BG_BOTTOM = (0.06, 0.07, 0.09)


class StlGLWidget(QOpenGLWidget):
    meshLoaded = QtCore.Signal(str)
    loadFailed = QtCore.Signal(str)
    rotationChanged = QtCore.Signal()
    resized = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(False)

        self.path: Path | None = None
        self.mesh: trimesh.Trimesh | None = None         # 文件里读出的网格（未旋转），保存时用它
        self.verts0: np.ndarray | None = None            # 展开顶点 / 法线（未旋转）
        self.normals0: np.ndarray | None = None
        self.verts: np.ndarray | None = None             # 旋转后用于显示
        self.normals: np.ndarray | None = None
        self.rot = np.eye(3)                             # 累计旋转矩阵（世界系）
        self.ops: list[tuple[str, int]] = []             # 旋转操作记录 [(轴, 角度)]
        self.bbox_min = np.zeros(3)
        self.bbox_max = np.zeros(3)
        self.n_faces = 0
        self.mesh_info = ""

        # 转台相机：绕 target 转，Z 轴朝上
        self.azimuth = 45.0
        self.elevation = 25.0
        self.distance = 5.0
        self.target = np.zeros(3)
        self.fov = 45.0
        self._home = None

        self.show_axes = True
        self.show_grid = True
        self.wireframe = False
        self.axis_len = 1.0
        self.grid_step = 0.1
        self.grid_half = 1.0

        self._last_pos = None
        self._button = None

        i18n.languageChanged.connect(self.retranslate)

    def retranslate(self) -> None:
        """语言切换：重算状态栏信息文字并重绘 HUD。"""
        if self.verts is not None:
            self._build_mesh_info()
            self.meshLoaded.emit(self.mesh_info)
        self.update()

    # ------------------------------------------------------------------ 加载
    def load(self, path) -> bool:
        path = Path(path)
        size = path.stat().st_size if path.is_file() else -1
        logger.info("加载 STL: {} ({:,} bytes)", path, size)
        t0 = time.perf_counter()
        try:
            verts, normals, mesh = load_stl(path)
        except Exception as e:  # noqa: BLE001
            logger.exception("加载失败: {}", path)
            self.loadFailed.emit(tr("gl.load_failed", name=path.name, err=e))
            return False
        if len(verts) == 0:
            logger.warning("文件没有三角面: {}", path)
            self.loadFailed.emit(tr("gl.no_triangles", name=path.name))
            return False
        self.path = path
        self.mesh = mesh
        self.verts0, self.normals0 = verts, normals
        self.rot = np.eye(3)
        self.ops = []
        self._apply_rotation(refit_home=True)
        self.rotationChanged.emit()
        ext = self.bbox_max - self.bbox_min
        logger.info(
            "加载完成: {} 三角面, 包围盒 min={} max={} 尺寸={} , 耗时 {:.0f} ms",
            f"{self.n_faces:,}",
            np.round(self.bbox_min, 4).tolist(),
            np.round(self.bbox_max, 4).tolist(),
            np.round(ext, 4).tolist(),
            (time.perf_counter() - t0) * 1000,
        )
        return True

    # ------------------------------------------------------------------ 旋转 / 保存
    def rotate(self, axis: str, deg: int) -> None:
        """把模型绕世界 axis 轴转 deg 度（绕原点）。"""
        if self.verts0 is None:
            return
        self.ops.append((axis, deg))
        self.rot = rot_matrix(axis, deg) @ self.rot
        self._apply_rotation()
        self.rotationChanged.emit()
        logger.info("旋转 {}{:+d}° | 序列={} | rpy={}",
                    axis, deg, self._ops_str(), self._rpy_str())

    def undo_rotation(self) -> None:
        if not self.ops:
            return
        undone = self.ops.pop()
        self.rot = np.eye(3)
        for axis, deg in self.ops:
            self.rot = rot_matrix(axis, deg) @ self.rot
        self._apply_rotation()
        self.rotationChanged.emit()
        logger.info("撤销 {}{:+d}° | 序列={} | rpy={}",
                    undone[0], undone[1], self._ops_str() or "(空)", self._rpy_str())

    def reset_rotation(self) -> None:
        if not self.ops:
            return
        logger.info("复位旋转，丢弃序列 {}", self._ops_str())
        self.ops = []
        self.rot = np.eye(3)
        self._apply_rotation()
        self.rotationChanged.emit()

    def _ops_str(self) -> str:
        return " ".join(f"{a}{d:+d}" for a, d in self.ops)

    def _rpy_str(self) -> str:
        r, p, y = self.rotation_rpy_deg()
        return f"({r:.0f}, {p:.0f}, {y:.0f})"

    @property
    def is_rotated(self) -> bool:
        return bool(self.ops)

    def rotation_rpy_deg(self) -> tuple[float, float, float]:
        return rotation_rpy_deg(self.rot)

    def save_as(self, path) -> bool:
        """把旋转后的网格写成新的 STL（二进制）。"""
        if self.mesh is None:
            return False
        path = Path(path)
        logger.info("另存为 STL: {} | 源={} | 序列={} | rpy={} | 面数={:,}",
                    path, self.path, self._ops_str() or "(未旋转)", self._rpy_str(), self.n_faces)
        t0 = time.perf_counter()
        try:
            T = np.eye(4)
            T[:3, :3] = self.rot
            out = self.mesh.copy()
            out.apply_transform(T)
            out.export(str(path), file_type="stl")
        except Exception as e:  # noqa: BLE001
            logger.exception("保存失败: {}", path)
            self.loadFailed.emit(tr("gl.save_failed", name=path.name, err=e))
            return False
        size = path.stat().st_size if path.is_file() else -1
        logger.info("保存完成: {:,} 三角面, {:,} bytes, 耗时 {:.0f} ms",
                    len(out.faces), size, (time.perf_counter() - t0) * 1000)
        self.meshLoaded.emit(tr("gl.saved", path=path, n=f"{len(out.faces):,}"))
        return True

    def _build_mesh_info(self) -> None:
        """按当前语言生成状态栏的网格信息文字。"""
        ext = self.bbox_max - self.bbox_min
        unit_hint = tr("gl.unit_mm") if ext.max() > 5.0 else tr("gl.unit_m")
        note = tr("gl.rotated_note") if self.ops else ""
        self.mesh_info = tr(
            "gl.mesh_info",
            name=self.path.name,
            note=note,
            n=f"{self.n_faces:,}",
            mn=f"{self.bbox_min[0]:.4g}, {self.bbox_min[1]:.4g}, {self.bbox_min[2]:.4g}",
            mx=f"{self.bbox_max[0]:.4g}, {self.bbox_max[1]:.4g}, {self.bbox_max[2]:.4g}",
            ext=f"{ext[0]:.4g} × {ext[1]:.4g} × {ext[2]:.4g}",
            unit=unit_hint,
        )

    def _apply_rotation(self, refit_home: bool = False) -> None:
        """用累计旋转矩阵重算显示用顶点/法线、包围盒、信息文字。"""
        R = self.rot.astype(np.float32)
        self.verts = np.ascontiguousarray(self.verts0 @ R.T)
        self.normals = np.ascontiguousarray(self.normals0 @ R.T)
        self.n_faces = len(self.verts) // 3
        self.bbox_min = self.verts.min(axis=0).astype(float)
        self.bbox_max = self.verts.max(axis=0).astype(float)
        self._build_mesh_info()
        self._update_scale()
        self.fit_view(remember_home=refit_home)
        self.meshLoaded.emit(self.mesh_info)
        self.update()

    def _update_scale(self):
        """根据模型尺寸决定轴长、网格间距（1-2-5 系列）。"""
        ext = float((self.bbox_max - self.bbox_min).max()) if self.verts is not None else 1.0
        far = float(np.abs(np.concatenate([self.bbox_min, self.bbox_max])).max()) if self.verts is not None else 1.0
        self.axis_len = max(ext, far) * 0.6 if ext > 0 else 1.0
        span = max(ext, far) * 1.5 or 1.0
        mag = 10 ** math.floor(math.log10(span / 10))
        for k in (1, 2, 5, 10):
            if span / (k * mag) <= 12:
                self.grid_step = k * mag
                break
        self.grid_half = self.grid_step * math.ceil(span / self.grid_step)

    def fit_view(self, remember_home=False):
        """把模型和原点一起放进视野。"""
        if self.verts is None:
            lo, hi = -np.ones(3), np.ones(3)
        else:
            lo = np.minimum(self.bbox_min, 0.0)
            hi = np.maximum(self.bbox_max, 0.0)
        center = (lo + hi) / 2
        radius = max(float(np.linalg.norm(hi - lo)) / 2, 1e-6)
        self.target = center
        self.distance = radius / math.sin(math.radians(self.fov) / 2) * 1.05
        if remember_home:
            self._home = (self.azimuth, self.elevation, self.distance, self.target.copy())
        self.update()

    def reset_view(self):
        if self._home is None:
            self.azimuth, self.elevation = 45.0, 25.0
            self.fit_view(remember_home=True)
            return
        self.azimuth, self.elevation, self.distance, t = self._home
        self.target = t.copy()
        self.update()

    # ------------------------------------------------------------------ 相机
    def _camera_vectors(self):
        az, el = math.radians(self.azimuth), math.radians(self.elevation)
        fwd = -np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
        eye = self.target - fwd * self.distance
        up_world = np.array([0.0, 0.0, 1.0])
        right = np.cross(fwd, up_world)
        right /= np.linalg.norm(right) or 1.0
        up = np.cross(right, fwd)
        return eye, fwd, right, up

    # ------------------------------------------------------------------ 拖放
    @staticmethod
    def _stl_urls(mime: QtCore.QMimeData):
        return [u.toLocalFile() for u in mime.urls()
                if u.isLocalFile() and u.toLocalFile().lower().endswith(".stl")]

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent):
        if e.mimeData().hasUrls() and self._stl_urls(e.mimeData()):
            e.acceptProposedAction()

    dragMoveEvent = dragEnterEvent

    def dropEvent(self, e: QtGui.QDropEvent):
        files = self._stl_urls(e.mimeData())
        if files:
            if len(files) > 1:
                logger.info("拖入 {} 个文件，只加载第一个", len(files))
            logger.info("拖放加载: {}", files[0])
            self.load(files[0])
            e.acceptProposedAction()

    # ------------------------------------------------------------------ 鼠标键盘
    def mousePressEvent(self, e):
        self._last_pos = e.position()
        self._button = e.button()

    def mouseReleaseEvent(self, e):
        self._last_pos = None
        self._button = None

    def mouseMoveEvent(self, e):
        if self._last_pos is None:
            return
        d = e.position() - self._last_pos
        self._last_pos = e.position()
        if self._button == QtCore.Qt.MouseButton.LeftButton:
            self.azimuth = (self.azimuth - d.x() * 0.4) % 360.0
            self.elevation = max(-89.0, min(89.0, self.elevation + d.y() * 0.4))
        elif self._button in (QtCore.Qt.MouseButton.RightButton, QtCore.Qt.MouseButton.MiddleButton):
            _, _, right, up = self._camera_vectors()
            h = max(self.height(), 1)
            per_px = 2 * self.distance * math.tan(math.radians(self.fov) / 2) / h
            self.target = self.target - right * d.x() * per_px + up * d.y() * per_px
        self.update()

    def wheelEvent(self, e):
        steps = e.angleDelta().y() / 120.0
        self.distance *= 0.88 ** steps
        self.distance = max(self.distance, 1e-5)
        self.update()

    def keyPressEvent(self, e):
        k = e.key()
        if k == QtCore.Qt.Key.Key_F:
            self.fit_view()
        elif k == QtCore.Qt.Key.Key_R:
            self.reset_view()
        elif k == QtCore.Qt.Key.Key_W:
            self.wireframe = not self.wireframe
        elif k == QtCore.Qt.Key.Key_G:
            self.show_grid = not self.show_grid
        elif k == QtCore.Qt.Key.Key_A:
            self.show_axes = not self.show_axes
        else:
            super().keyPressEvent(e)
            return
        self.update()

    # ------------------------------------------------------------------ OpenGL
    def initializeGL(self):
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE, GL.GL_TRUE)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, (0.25, 0.25, 0.25, 1.0))
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, (0.85, 0.85, 0.85, 1.0))
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, (0.3, 0.3, 0.3, 1.0))
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SPECULAR, (0.3, 0.3, 0.3, 1.0))
        GL.glMaterialf(GL.GL_FRONT_AND_BACK, GL.GL_SHININESS, 32.0)

    def resizeGL(self, w, h):
        super().resizeGL(w, h)
        self.resized.emit()

    def _px(self):
        dpr = self.devicePixelRatio()
        return int(self.width() * dpr), int(self.height() * dpr), dpr

    def paintGL(self):
        painter = QtGui.QPainter(self)
        painter.beginNativePainting()
        try:
            labels = self._draw_scene()
        finally:
            painter.endNativePainting()
        self._draw_hud(painter, labels)
        painter.end()

    def _draw_scene(self):
        w, h, _ = self._px()
        GL.glViewport(0, 0, w, h)
        GL.glClearColor(*BG_BOTTOM, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        # QPainter 每帧会改掉这些状态，重新设一遍
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glEnable(GL.GL_NORMALIZE)
        self._draw_background()

        aspect = w / max(h, 1)
        near, far = self.distance * 0.01, self.distance * 50.0
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(self.fov, aspect, near, far)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        # 灯光跟着相机走（在 lookAt 之前设置 → 相机坐标系）
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, (0.4, 0.6, 1.0, 0.0))
        eye, _, _, up = self._camera_vectors()
        GLU.gluLookAt(*eye, *self.target, *up)

        if self.show_grid:
            self._draw_grid()
        if self.verts is not None:
            self._draw_mesh()
        labels = []
        if self.show_axes:
            labels += self._draw_axes(self.axis_len, overlay=True)
        labels += self._draw_corner_triad()
        GL.glDisable(GL.GL_DEPTH_TEST)   # 接下来 QPainter 画文字，不能被深度测试挡住
        return labels

    def _draw_background(self):
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, 1, 0, 1, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glBegin(GL.GL_QUADS)
        GL.glColor3f(*BG_BOTTOM); GL.glVertex2f(0, 0); GL.glVertex2f(1, 0)
        GL.glColor3f(*BG_TOP); GL.glVertex2f(1, 1); GL.glVertex2f(0, 1)
        GL.glEnd()
        GL.glEnable(GL.GL_DEPTH_TEST)

    def _draw_grid(self):
        GL.glDisable(GL.GL_LIGHTING)
        GL.glLineWidth(1.0)
        n = int(round(self.grid_half / self.grid_step))
        GL.glBegin(GL.GL_LINES)
        for i in range(-n, n + 1):
            v = i * self.grid_step
            major = i % 5 == 0
            GL.glColor4f(0.55, 0.58, 0.62, 0.40 if major else 0.15)
            GL.glVertex3f(v, -self.grid_half, 0); GL.glVertex3f(v, self.grid_half, 0)
            GL.glVertex3f(-self.grid_half, v, 0); GL.glVertex3f(self.grid_half, v, 0)
        GL.glEnd()

    def _draw_mesh(self):
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glColorMaterial(GL.GL_FRONT_AND_BACK, GL.GL_AMBIENT_AND_DIFFUSE)
        GL.glColor3f(*MESH_COLOR)
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE if self.wireframe else GL.GL_FILL)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)
        GL.glVertexPointer(3, GL.GL_FLOAT, 0, self.verts)
        GL.glNormalPointer(GL.GL_FLOAT, 0, self.normals)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.verts))
        GL.glDisableClientState(GL.GL_NORMAL_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        GL.glDisable(GL.GL_LIGHTING)

    def _draw_axes(self, length: float, overlay: bool):
        """画 XYZ 三色轴，返回 [(屏幕x, 屏幕y, 文字, 颜色)] 供 QPainter 标注。
        overlay=True 时关闭深度测试，轴总是显示在模型之上。"""
        GL.glDisable(GL.GL_LIGHTING)
        if overlay:
            GL.glDisable(GL.GL_DEPTH_TEST)
        # 负半轴：细、淡
        GL.glLineWidth(1.0)
        GL.glBegin(GL.GL_LINES)
        for name, d in AXIS_DIRS.items():
            GL.glColor4f(*AXIS_COLORS[name], 0.35)
            GL.glVertex3f(0, 0, 0)
            GL.glVertex3f(-d[0] * length * 0.5, -d[1] * length * 0.5, -d[2] * length * 0.5)
        GL.glEnd()
        # 正半轴：粗
        GL.glLineWidth(3.0)
        GL.glBegin(GL.GL_LINES)
        for name, d in AXIS_DIRS.items():
            GL.glColor4f(*AXIS_COLORS[name], 1.0)
            GL.glVertex3f(0, 0, 0)
            GL.glVertex3f(d[0] * length, d[1] * length, d[2] * length)
        GL.glEnd()
        # 原点小球
        GL.glPointSize(9.0)
        GL.glBegin(GL.GL_POINTS)
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
        GL.glVertex3f(0, 0, 0)
        GL.glEnd()
        GL.glLineWidth(1.0)
        if overlay:
            GL.glEnable(GL.GL_DEPTH_TEST)
        return self._project_labels(length)

    def _project_labels(self, length: float):
        mv = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
        pj = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
        vp = GL.glGetIntegerv(GL.GL_VIEWPORT)
        _, h, dpr = self._px()
        out = []
        for name, d in AXIS_DIRS.items():
            x, y, z = GLU.gluProject(d[0] * length * 1.08, d[1] * length * 1.08, d[2] * length * 1.08, mv, pj, vp)
            if 0.0 < z < 1.0:
                out.append((x / dpr, (h - y) / dpr, name, AXIS_COLORS[name]))
        return out

    def _draw_corner_triad(self):
        """右下角固定大小的小三轴，只反映旋转。"""
        w, h, dpr = self._px()
        size = int(110 * dpr)
        margin = int(12 * dpr)
        GL.glViewport(w - size - margin, margin, size, size)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1.3, 1.3, -1.3, 1.3, -3, 3)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        _, fwd, _, up = self._camera_vectors()
        GLU.gluLookAt(*(-fwd * 2.0), 0, 0, 0, *up)
        labels = self._draw_axes(0.9, overlay=False)
        GL.glViewport(0, 0, w, h)
        return labels

    def _draw_hud(self, painter: QtGui.QPainter, labels):
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        for x, y, name, (r, g, b) in labels:
            painter.setPen(QtGui.QColor.fromRgbF(r, g, b))
            painter.drawText(QtCore.QPointF(x - 5, y + 5), name)

        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(235, 235, 235))
        if self.verts is None:
            big = painter.font()
            big.setPointSize(16)
            painter.setFont(big)
            painter.setPen(QtGui.QColor(200, 200, 200, 200))
            painter.drawText(self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, tr("gl.drop_here"))
            painter.setFont(font)
        tips = tr("gl.tips", step=f"{self.grid_step:g}")
        painter.setPen(QtGui.QColor(190, 190, 190))
        painter.drawText(QtCore.QPointF(10, self.height() - 10), tips)
