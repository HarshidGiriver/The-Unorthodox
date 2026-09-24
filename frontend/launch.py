"""Installed console entrypoint: kintsugi."""

from pathlib import Path
import subprocess
import sys


def main():
    app = Path(__file__).with_name("app.py")
    raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(app),
                                     "--server.address=127.0.0.1", "--server.enableCORS=true", "--server.enableXsrfProtection=true", *sys.argv[1:]]))
