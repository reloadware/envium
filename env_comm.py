from pathlib import Path

import envo

root = Path(__file__).parent.absolute()
envo.add_source_roots([root])

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from envo import Env, Namespace, VirtualEnv, inject, run

# Declare your command namespaces here
# like this:
p = Namespace("p")


@dataclass
class PythonVersion:
    ver: str

    @property
    def id(self) -> str:
        return self.ver.replace(".", "-")


class EnviumCommEnv(Env, VirtualEnv):
    class Meta(Env.Meta):
        root: Path = root
        verbose_run: bool = True
        name = "envium"

    class Environ(Env.Environ, VirtualEnv.Environ):
        ...

    class Ctx(Env.Ctx, VirtualEnv.Ctx):
        ...

    e: Environ

    pip_ver: str
    poetry_ver: str
    envo_ver = "0.9.9.13"
    supported_versions = [
        PythonVersion("3.6"),
        PythonVersion("3.7"),
        PythonVersion("3.8"),
        PythonVersion("3.9"),
    ]

    def init(self) -> None:
        super().init()
        self.pip_ver = "21.0.1"
        self.poetry_ver = "1.1.7"
        self.black_ver = "21.6b0"

    @p.command
    def bootstrap(self) -> None:
        run("rm -rf .venv")
        run(f"pip install pip=={self.pip_ver}")
        run(f"pip install poetry=={self.poetry_ver}")
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install --no-root")

    @p.command
    def test(self) -> None:
        run("pytest tests")

    @p.command
    def mypy(self) -> None:
        inject("mypy .")

    @p.command
    def black(self) -> None:
        inject("isort .")
        inject("black .")


ThisEnv = EnviumCommEnv
