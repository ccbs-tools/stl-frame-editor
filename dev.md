# 开发

规范：`../dev-rules/CONVENTIONS.md`。

## 环境

本项目用 [uv](https://docs.astral.sh/uv/) 管理 Python 与依赖，不需要单独安装 Python。

```powershell
uv sync --group dev                        # 安装运行依赖 + pyinstaller
uv run python -m stl_frame_editor          # 源码运行
uv run pyinstaller main.spec --noconfirm   # 本地打包 → dist\stl-frame-editor\stl-frame-editor.exe
```

运行时文件：

| 内容 | 位置 |
| --- | --- |
| 日志 | `%APPDATA%\ccbs\stl-frame-editor\logs\app.log`（10 MB 轮转，保留 3 个）。0.2.0 及之前在 `~/.ccbs/stl-frame-editor/`，可手动删除 |
| 语言设置 | QSettings（注册表 `HKCU\Software\ccbs\stl-frame-editor`）。0.2.0 及之前在 `HKCU\Software\CCBS\CCBS STL View`，不迁移 |

## 目录

```
run.py                       PyInstaller 入口（转调 stl_frame_editor.__main__:main）
main.spec                    PyInstaller onedir 配置（裁掉未用的 Qt 模块；3D 工具保留 QtOpenGL）
stl_frame_editor/
  __init__.py                APP_NAME、__version__
  __main__.py                入口：日志初始化、QSurfaceFormat、QApplication、主窗口
  i18n.py                    中英文文案表，tr() / i18n.languageChanged
  log.py                     loguru 日志；接管未捕获异常、Qt 消息、stdlib logging
  changelog.py               版本历史（Release 说明从这里生成）+ GitHub Releases 检查更新
  version_dialogs.py         版本介绍 / 检查更新对话框
  main_window.py             主窗口、菜单栏、应用图标
  gl_widget.py               OpenGL 视口（网格 / 坐标轴 / 相机 / 拖放）
  panel.py                   右上角旋转面板
  mesh.py                    STL 读取、旋转矩阵、rpy
assets/                      icon.ico / icon.png 与 README 截图
README.md / README.zh.md     面向用户的说明（英文 / 中文）
```

## 文案

所有界面文字集中在 `stl_frame_editor/i18n.py` 的 `_STRINGS`，中英两张表的键必须一致。新增文案时：

1. 两张表各加一条，键名用 `模块.含义` 形式（如 `dialog.open_title`、`gl.saved`）。
2. 代码里用 `tr("key", **kwargs)` 取文案；动态刷新的控件在所属类的 `retranslate()` 里更新。

日志（`logger.*`）统一英文，不走 i18n。

## 发版

检查更新时，本地版本只读 `stl_frame_editor/__init__.py` 的 `__version__`。云端版本来自 GitHub Release 的 tag（去掉开头的 `v`），不是代码里的字符串。

版本号有三处，发版时一起改、保持一致（CI 在推 tag 时会校验）：

1. `stl_frame_editor/__init__.py` 的 `__version__`：检查更新用的本地版本。
2. `pyproject.toml` 的 `version`：GitHub Actions 打包 zip 名用这个，例如 `stl-frame-editor-v0.2.1-windows-x64.zip`。
3. `stl_frame_editor/changelog.py` 的 `RELEASES`：在最前面加一条版本说明，「版本介绍」对话框会显示它。中英文 `notes` 都要写。

改完后提交，再推送同名 tag：

```powershell
git tag v0.2.1
git push origin v0.2.1
```

源码仓库私有，`.github/workflows/build.yml` 在 `v*` tag 上打包并通过 GitHub App（`ccbs-release-bot`，Secrets `RELEASE_APP_ID` / `RELEASE_APP_PRIVATE_KEY`）把 zip + `SHA256SUMS.txt` 发布到公开仓库 `ccbs-tools/stl-frame-editor-release`；在 Actions 页面手动 "Run workflow" 则只打包，产物在 Artifacts 里保留 7 天。
