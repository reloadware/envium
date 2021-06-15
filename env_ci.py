import os  # noqa: F401

from typing import List, Dict, Any, Optional, Tuple  # noqa: F401

from pathlib import Path

from dataclasses import dataclass  # noqa: F401

import envo  # noqa: F401

from envo import (  # noqa: F401
    logger,
    command,
    context,
    run,
    precmd,
    onstdout,
    onstderr,
    postcmd,
    onload,
    oncreate,
    onunload,
    ondestroy,
    boot_code,
    on_partial_reload,
    Plugin,
    VirtualEnv,
    UserEnv,
    Namespace,
    Source,
    console,
    var,
    computed_var
)

# Declare your command namespaces here
# like this:
pr = Namespace("pr")


class EnviumCiEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root: Path = Path(__file__).parent.absolute()
        stage: str = "ci"
        emoji: str = "🧪"
        parents: List[str] = ["env_comm.py"]
        plugins: List[Plugin] = []
        sources: List[Source] = []
        name: str = "envium"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []
        verbose_run: bool = True

    class Environ:
        ...
    e: Environ

    def __init__(self) -> None:
        # Define your variables here
        ...

    @pr.command
    def bootstrap(self) -> None:
        run("mkdir -p workspace")
        super().bootstrap()

    @pr.command
    def test(self) -> None:
        run("pytest -v --cov-report html --cov=envium tests --junitxml=test-results/junit.xml")

    @pr.command
    def build(self) -> None:
        run("poetry build")

    @pr.command
    def publish(self) -> None:
        run("poetry publish --username $PYPI_USERNAME --password $PYPI_PASSWORD")

    @pr.command
    def rstcheck(self) -> None:
        pass
        # run("rstcheck README.rst | tee ./workspace/rstcheck.txt")

    @pr.command
    def flake(self) -> None:
        pass
        # run("flake8 . | tee ./workspace/flake8.txt")

    @pr.command
    def check_black(self) -> None:
        pass
        # run("black --check . | tee ./workspace/black.txt")

    @pr.command
    def mypy(self) -> None:
        pass
        # run("mypy . | tee ./workspace/mypy.txt")

    @pr.command
    def generate_version(self) -> None:
        import toml

        config = toml.load(str(self.meta.root / "pyproject.toml"))
        version: str = config["tool"]["poetry"]["version"]

        version_file = self.meta.root / "envium/__version__.py"
        Path(version_file).touch()

        version_file.write_text(f'__version__ = "{version}"\n')


Env = EnviumCiEnv
