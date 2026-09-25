"""Windowed PyInstaller entry point for SimControlsManager.exe."""

from sim_controls_manager.gui import main as gui_main


if __name__ == "__main__":
    raise SystemExit(gui_main())
