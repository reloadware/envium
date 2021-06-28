from pathlib import Path

import envo  # noqa: F401

root = Path(__file__).parent.absolute()
envo.add_source_roots([root])

from dataclasses import dataclass  # noqa: F401
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

import envo  # noqa: F401
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
p = Namespace("p")


class EnviumCiEnv(ParentEnv):  # type: ignore
    class Meta(ParentEnv.Meta):  # type: ignore
        root: Path = root
        stage: str = "ci"
        emoji: str = "🧪"
        name: str = "envium"

    class Environ(ParentEnv.Environ):
        ...

    e: Environ

    ci_config_templ: Path
    config: Path

    def init(self) -> None:
        super().init()

        self.ci_config_templ = self.meta.root / "config.yml.templ"
        self.config = self.meta.root / ".circleci/config.yml"

    @p.command
    def bootstrap(self) -> None:
        run("mkdir -p workspace")
        super().bootstrap()

    @p.command
    def test(self) -> None:
        run(
            "pytest -v --cov-report html --cov=envium tests --junitxml=test-results/junit.xml"
        )

    @p.command
    def build(self) -> None:
        run("poetry build")

    @p.command
    def publish(self) -> None:
        run("poetry publish --username $PYPI_USERNAME --password $PYPI_PASSWORD")

    @p.command
    def rstcheck(self) -> None:
        pass
        # run("rstcheck README.rst | tee ./workspace/rstcheck.txt")

    @p.command
    def flake(self) -> None:
        pass
        # run("flake8 . | tee ./workspace/flake8.txt")

    @p.command
    def check_black(self) -> None:
        run("black --check . | tee ./workspace/black.txt")

    @p.command
    def mypy(self) -> None:
        run("mypy . | tee ./workspace/mypy.txt")

    @p.command
    def render(self) -> None:
        from jinja2 import StrictUndefined, Template

        ctx = {
            "supported_versions": self.supported_versions,
            "envo_version": self.envo_version,
        }

        templ = Template(self.ci_config_templ.read_text(), undefined=StrictUndefined)
        self.config.write_text(templ.render(**ctx))

    @p.command
    def generate_version(self) -> None:
        import toml

        config = toml.load(str(self.meta.root / "pyproject.toml"))
        version: str = config["tool"]["poetry"]["version"]

        version_file = self.meta.root / "envium/__version__.py"
        Path(version_file).touch()

        version_file.write_text(f'__version__ = "{version}"\n')


ThisEnv = EnviumCiEnv
