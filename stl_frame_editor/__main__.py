"""入口：python -m stl_frame_editor [xxx.stl]

操作:
    左键拖动   旋转（绕目标点转台式旋转，Z 轴朝上）
    右键/中键  平移
    滚轮       缩放
    F 适配  R 复位  W 线框  G 网格  A 坐标轴  Ctrl+O 打开

右上角面板：绕世界 X / Y / Z 轴转 ±90°（绕原点，右手定则），可撤销 / 复位，
显示累计旋转矩阵和等效 URDF rpy，"另存为 STL" 写成新文件（原文件不动）。
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    import platform

    from .log import logger, setup_logging

    log_file = setup_logging()

    from PySide6 import QtCore, QtGui, QtWidgets

    from . import __version__
    from .i18n import i18n
    from .main_window import MainWindow, make_app_icon

    args = sys.argv[1:] if argv is None else argv
    logger.info("=" * 60)
    logger.info(
        "stl-frame-editor v{} 启动 | python {} | PySide6 {} | {} | frozen={}",
        __version__, platform.python_version(), QtCore.__version__,
        platform.platform(), bool(getattr(sys, "frozen", False)),
    )
    logger.info("日志文件: {}", log_file)
    logger.debug("argv: {}", args)

    # Windows：不用 Python 默认 AppID，任务栏才会显示本程序图标而不是 python.exe
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.ccbs.stl_view")
        except Exception:  # noqa: BLE001
            pass

    fmt = QtGui.QSurfaceFormat()
    fmt.setSamples(4)
    fmt.setDepthBufferSize(24)
    fmt.setProfile(QtGui.QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    QtGui.QSurfaceFormat.setDefaultFormat(fmt)

    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("CCBS")
    app.setApplicationName("CCBS STL View")
    i18n.load()                      # 读取上次选的语言（首次默认英文）
    icon = make_app_icon()
    app.setWindowIcon(icon)

    initial = args[0] if args else None
    if initial:
        logger.info("命令行指定启动文件: {}", initial)
    win = MainWindow(initial)
    win.setWindowIcon(icon)
    win.show()
    code = app.exec()
    logger.info("程序退出 code={}", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
