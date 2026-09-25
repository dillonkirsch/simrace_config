"""Windowed PyInstaller entry point for SimControlsManager.exe."""

import sys

from sim_controls_manager.gui import main as gui_main


if __name__ == "__main__":
    smoke_test = sys.argv[1:] == ["--smoke-test"]
    if smoke_test:
        try:
            raise SystemExit(gui_main(smoke_test=True))
        except Exception:
            raise SystemExit(1) from None
    raise SystemExit(gui_main())
