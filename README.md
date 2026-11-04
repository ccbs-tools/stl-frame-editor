# STL Coordinate Frame Editor

**English** | [中文](README.zh.md)

Drag a `.stl` file into the window to view it, with a tri-color XYZ axis drawn at the origin.
The panel in the top-right rotates the model ±90° about the world X/Y/Z axes (about the origin, right-hand rule),
shows the accumulated rotation matrix and the equivalent URDF `rpy`, and **Save As STL** writes a new file
(the original is never touched). The menu bar supports switching between English and Chinese at runtime.

| Empty window (drop target) | STL loaded |
|---|---|
| ![Empty view](assert/soft-empty-view.png) | ![Loaded view](assert/open-stl-view.png) |

### Demo

https://private-user-images.githubusercontent.com/34444109/694237544-cf939573-5380-42bf-baad-11ce17f5d5cb.mp4

Dependencies: PySide6, PyOpenGL, numpy, trimesh.

## Install

```bash
cd path/to/stl-frame-editor
uv venv && uv pip install -e .
```

## Run

```bash
stl-frame-editor [xxx.stl]
# or
python -m stl_frame_editor [xxx.stl]
```

## Controls

| Action | Description |
|------|------|
| Left drag | Rotate (turntable, Z up) |
| Right / Middle drag | Pan |
| Wheel | Zoom |
| `F` / `R` | Fit view / back to initial view |
| `W` / `G` / `A` | Toggle wireframe / ground grid / origin axes |
| `Ctrl+O` | Open file |

Red = X, Green = Y, Blue = Z. The small axis gizmo in the bottom-right always shows the current orientation.

## Package (onedir)

```bash
uv pip install pyinstaller
uv run pyinstaller main.spec --noconfirm
# Output: dist/stl-frame-editor/stl-frame-editor.exe, with dependencies alongside it
```

## Structure

```
stl_frame_editor/
  __main__.py     entry point main()
  main_window.py  main window, menus, app icon
  gl_widget.py    OpenGL viewport (grid / axes / camera / drag-drop)
  panel.py        top-right rotation panel
  mesh.py         STL loading, rotation matrix, rpy
  i18n.py         language strings and runtime switching
run.py            PyInstaller entry
main.spec         PyInstaller config
```
