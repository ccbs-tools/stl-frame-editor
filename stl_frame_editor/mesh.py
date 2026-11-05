"""STL 读取与旋转矩阵。"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh

AXIS_COLORS = {"X": (0.92, 0.20, 0.20), "Y": (0.20, 0.80, 0.20), "Z": (0.25, 0.45, 1.00)}
AXIS_DIRS = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


def expand_mesh(mesh: trimesh.Trimesh):
    """把网格展开成按三角形排列的顶点和法线（float32, N*3 x 3），供 glDrawArrays 使用。"""
    verts = mesh.vertices[mesh.faces].reshape(-1, 3).astype(np.float32)
    normals = np.repeat(mesh.face_normals, 3, axis=0).astype(np.float32)
    normals = np.nan_to_num(normals)
    return np.ascontiguousarray(verts), np.ascontiguousarray(normals)


def load_stl(path: Path):
    """读取 STL（ascii / binary 都行），返回按三角形展开的顶点和法线（float32, N*3 x 3）。"""
    mesh = trimesh.load(str(path), file_type="stl", force="mesh", process=False)
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)
    verts, normals = expand_mesh(mesh)
    return verts, normals, mesh


def rot_matrix(axis: str, deg: int) -> np.ndarray:
    """绕世界 X/Y/Z 轴旋转 deg 度（90 的整数倍时元素是精确的 0/±1）。"""
    a = math.radians(deg)
    c, s = round(math.cos(a), 12), round(math.sin(a), 12)
    if axis == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)
    if axis == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def rotation_rpy_deg(rot: np.ndarray) -> tuple[float, float, float]:
    """旋转矩阵的等效 URDF rpy（固定轴 X→Y→Z，度）。"""
    T = np.eye(4)
    T[:3, :3] = rot
    r, p, y = trimesh.transformations.euler_from_matrix(T, "sxyz")
    return math.degrees(r), math.degrees(p), math.degrees(y)
