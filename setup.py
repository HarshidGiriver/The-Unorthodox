"""Bundle source-tree resources into the wheel without duplicating source assets."""

from pathlib import Path
from shutil import copy2
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithResources(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
        for folder in ("assets", "models", "data/raw"):
            for source in (root / folder).glob("*"):
                if source.is_file():
                    destination = Path(self.build_lib) / "backend" / "resources" / folder / source.name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    copy2(source, destination)


setup(cmdclass={"build_py": BuildWithResources})
