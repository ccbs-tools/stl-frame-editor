"""PyInstaller 打包入口（等价于 python -m ccbs_stl_frame_editor）。"""

from ccbs_stl_frame_editor.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
