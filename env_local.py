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
    Namespace,
    Plugin,
    Source,
    boot_code,
    command,
    computed_var,
    console,
    context,
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

from env_comm import EnviumCommEnv as ParentEnv

# Declare your command namespaces here
# like this:
# my_namespace = Namespace("my_namespace")


p = Namespace("p")


class EnviumLocalEnv(ParentEnv):  # type: ignore
    class Meta(ParentEnv.Meta):  # type: ignore
        root: Path = Path(__file__).parent.absolute()
        stage: str = "local"
        emoji: str = "🐣"
        name: str = "envium"

    class Environ(ParentEnv.Environ):
        ...

    e: Environ

    python_ver = "3.9.5"

    @p.command
    def bootstrap(self) -> None:
        path_before = os.environ["PATH"]
        os.environ[
            "PATH"
        ] = f"/home/kwazar/.pyenv/versions/{self.python_ver}/bin/:{os.environ['PATH']}"
        run(f"python -m venv .venv")
        os.environ["PATH"] = f"{self.python_ver}/bin/:{os.environ['PATH']}"
        super().bootstrap()

        os.environ["PATH"] = path_before


ThisEnv = EnviumLocalEnv
