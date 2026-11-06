# 发版

检查更新时，本地版本只读 `stl_frame_editor/__init__.py` 的 `__version__`。云端版本来自 GitHub Release 的 tag（去掉开头的 `v`），不是代码里的字符串。

发版时这三处要一起改，版本号保持一致：

1. `stl_frame_editor/__init__.py` 的 `__version__`：检查更新用的本地版本。
2. `pyproject.toml` 的 `version`：GitHub Actions 打包 zip 名用这个，例如 `stl-frame-editor-v0.1.1-windows-x64.zip`。
3. `stl_frame_editor/changelog.py` 的 `RELEASES`：在最前面加一条版本说明，「版本介绍」对话框会显示它。中英文 `notes` 都要写。

改完后提交，再推送同名 tag，例如 `v0.1.1`。`.github/workflows/build.yml` 在 `v*` tag 上会打包并发布 Release。
