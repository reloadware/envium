from pathlib import Path

import envo

root = Path(__file__).parent.absolute()
envo.add_source_roots([root])

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from envo import Env, VirtualEnv, inject, run, command
from envo import venv_utils

venv_utils.PredictedVenv(envo.get_repo_root(), ".venv").activate()


# Declare your command namespaces here
# like this:


class EnviumCommEnv(Env):
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
    envo_ver = "1.5.2"
    supported_versions = ["3.8", "3.9", "3.10", "3.11"]

    def init(self) -> None:
        super().init()
        self.pip_ver = "23.1.2"
        self.poetry_ver = "1.5.1"
        self.black_ver = "21.6b0"

    @command
    def p__bootstrap(self) -> None:
        run("rm -rf .venv")
        run(f"pip install pip=={self.pip_ver}")
        run(f"pip install poetry=={self.poetry_ver}")
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install --no-root")

    @command
    def p__test(self) -> None:
        run("pytest tests")

    @command
    def p__mypy(self) -> None:
        inject("mypy .")

    @command
    def p__black(self) -> None:
        inject("isort .")
        inject("black .")


ThisEnv = EnviumCommEnv
