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
# my_namespace = Namespace("my_namespace")


class EnvoClientLocalEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root: Path = Path(__file__).parent.absolute()
        stage: str = "local"
        emoji: str = "🐣"
        parents: List[str] = ["env_comm.py"]
        plugins: List[Plugin] = []
        sources: List[Source] = []
        name: str = "envium"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []
        verbose_run: bool = True

    # Declare your variables here

    def __init__(self) -> None:
        # Define your variables here
        ...


    # Define your commands, hooks and properties here


Env = EnvoClientLocalEnv
