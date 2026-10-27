"""Punto de entrada para PyInstaller y para ejecutar desde el código fuente."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from cray_flp_analyzer.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["gui"]))
