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


class EnvoClientCommEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root: Path = Path(__file__).parent.absolute()
        stage: str = "comm"
        emoji: str = "👌"
        parents: List[str] = []
        plugins: List[Plugin] = [VirtualEnv]
        sources: List[Source] = []
        name: str = "envium"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []
        verbose_run: bool = True

    class Environ:
        ...
    e: Environ

    pip_version: str
    poetry_version: str

    def __init__(self) -> None:
        self.pip_version = "21.0.1"
        self.poetry_version = "1.0.10"

    @pr.command
    def bootstrap(self) -> None:
        run(f"pip install pip=={self.pip_version}")
        run(f"pip install poetry=={self.poetry_version}")
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install --no-root")

    @pr.command
    def test(self) -> None:
        run("pytest tests")

    # Define your commands, hooks and properties here


Env = EnvoClientCommEnv
