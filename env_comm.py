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


class EnvoClientCommEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root: Path = Path(__file__).parent.absolute()
        stage: str = "comm"
        emoji: str = "👌"
        parents: List[str] = []
        plugins: List[Plugin] = []
        sources: List[Source] = []
        name: str = "envo-client"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []
        verbose_run: bool = False

    # Declare your variables here

    def __init__(self) -> None:
        # Define your variables here
        ...

    # Define your commands, hooks and properties here


Env = EnvoClientCommEnv