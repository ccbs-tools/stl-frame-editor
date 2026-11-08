# stl-frame-editor — AI 协作说明

本项目遵循 CCBS 桌面工具统一规范（Python + PySide6 + uv + PyInstaller + GitHub Actions）。

- 完整规范：`../dev-rules/CONVENTIONS.md`（与本仓库同级的 `dev-rules` 目录）。
- 可复制的模板文件：`../dev-rules/templates/`。
- 如果 `../dev-rules` 不存在：`git clone https://github.com/ccbs-tools/dev-rules.git ../dev-rules`。

改动涉及下列内容前先读规范对应章节：界面文案（i18n）、日志、版本号与 `changelog.py`、`main.spec` 打包、`.github/workflows/build.yml`、README 结构。

要点速记：

- 界面文字全部走 `stl_frame_editor/i18n.py` 的 `tr()`，中英两张表键一致；控件文字在 `retranslate()` 里设置。
- 日志用 `from .log import logger`，文本英文，不记录任何秘密。
- 发版改三处版本号：`stl_frame_editor/__init__.py`、`pyproject.toml`、`changelog.py` 的 `RELEASES`；推 `vX.Y.Z` tag 触发 CI。
- 代码注释与 docstring 用中文。
