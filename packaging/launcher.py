"""PyInstaller entry point for SimControlsManager.exe."""

import sys

from sim_controls_manager.cli import main as cli_main
from sim_controls_manager.gui import main as gui_main


if __name__ == "__main__":
    raise SystemExit(cli_main() if len(sys.argv) > 1 else gui_main())
