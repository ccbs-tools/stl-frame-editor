# CCBS STL View（STL 坐标系修改器）

把 `.stl` 拖进窗口即可显示，原点处标注 XYZ 三色轴；右上角面板可把模型绕世界 X/Y/Z 轴转 ±90°（绕原点，右手定则），
显示累计旋转矩阵和等效 URDF rpy，"另存为 STL" 写出新文件（原文件不动）。

依赖：PySide6、PyOpenGL、numpy、trimesh。

## 安装 / 运行

```bash
cd software/python/stl-frame-editor
uv venv && uv pip install -e .
stl-frame-editor [xxx.stl]
# 或
python -m stl_frame_editor [xxx.stl]
```

## 操作

| 操作 | 说明 |
|------|------|
| 左键拖动 | 旋转（转台式，Z 轴朝上） |
| 右键 / 中键 | 平移 |
| 滚轮 | 缩放 |
| `F` / `R` | 适配视角 / 回到初始视角 |
| `W` / `G` / `A` | 线框 / 地面网格 / 原点坐标轴 开关 |
| `Ctrl+O` | 打开文件 |

红 = X，绿 = Y，蓝 = Z。右下角小三轴始终显示当前朝向。

## 打包（onedir）

```bash
uv pip install pyinstaller
uv run pyinstaller main.spec --noconfirm
# 输出 dist/stl-frame-editor/stl-frame-editor.exe，依赖在 stl-frame-editor-lib/
```

## 结构

```
stl_frame_editor/
  __main__.py     入口 main()
  main_window.py  主窗口、菜单、应用图标
  gl_widget.py    OpenGL 视口（网格 / 坐标轴 / 相机 / 拖放）
  panel.py        右上角旋转面板
  mesh.py         STL 读取、旋转矩阵、rpy
run.py            PyInstaller 入口
main.spec         PyInstaller 配置
```
