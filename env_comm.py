import os
from pathlib import Path

import envo  # noqa: F401

root = Path(__file__).parent.absolute()
envo.add_source_roots([root])

import os  # noqa: F401
from dataclasses import dataclass  # noqa: F401
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

from envo import VirtualEnv  # noqa: F401
from envo import (
    Env,
    Namespace,
    Plugin,
    Source,
    boot_code,
    command,
    computed_var,
    console,
    context,
    inject,
    logger,
    on_partial_reload,
    oncreate,
    ondestroy,
    onload,
    onstderr,
    onstdout,
    onunload,
    postcmd,
    precmd,
    run,
    var,
)

# Declare your command namespaces here
# like this:
p = Namespace("p")


@dataclass
class PythonVersion:
    ver: str

    @property
    def id(self) -> str:
        return self.ver.replace(".", "-")


class EnviumCommEnv(Env, VirtualEnv):  # type: ignore
    class Meta(Env.Meta):  # type: ignore
        root: Path = root
        verbose_run: bool = True

    class Environ(Env.Environ, VirtualEnv.Environ):
        ...

    e: Environ

    pip_version: str
    poetry_version: str
    envo_version = "0.9.9.13"
    supported_versions = [
        PythonVersion("3.6"),
        PythonVersion("3.7"),
        PythonVersion("3.8"),
        PythonVersion("3.9"),
    ]

    def init(self) -> None:
        super().init()
        self.pip_version = "21.0.1"
        self.poetry_version = "1.1.7"

    @p.command
    def bootstrap(self) -> None:
        run(f"pip install pip=={self.pip_version}")
        run(f"pip install poetry=={self.poetry_version}")
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
