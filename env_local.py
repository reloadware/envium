import os
from pathlib import Path
from textwrap import dedent

import envo

root = Path(__file__).parent.absolute()
envo.add_source_roots([root])

import os
from typing import Any, Dict, List, Optional, Tuple

from envo import Namespace, VirtualEnv, run

from env_comm import EnviumCommEnv as ParentEnv

# Declare your command namespaces here
# like this:
# my_namespace = Namespace("my_namespace")

p = Namespace("p")


class EnviumLocalEnv(ParentEnv):
    class Meta(ParentEnv.Meta):
        stage: str = "local"
        emoji: str = "🐣"

    class Environ(ParentEnv.Environ):
        ...

    e: Environ

    python_ver = "3.9.5"

    def init(self) -> None:
        super().init()

        self.ci_template = self.meta.root / ".github/workflows/test.yml.templ"
        self.ci_out = self.meta.root / ".github/workflows/test.yml"

    @p.command
    def render_ci(self) -> None:
        from jinja2 import StrictUndefined, Template

        bootstrap_code = dedent(
            """
        - uses: actions/checkout@v2
        - name: Set up Python
          uses: actions/setup-python@v2
          with:
            {%- raw %}
            python-version: ${{ matrix.python_version }}
            {%- endraw %}
        - uses: gerbal/always-cache@v1.0.3
          id: pip-cache
          with:
            path: ~/.cache/pip
            key: pip-cache-{{ pip_ver }}-{{ poetry_ver }}-{{ envo_ver }}
            restore-keys: pip-cache-
        - run: pip install pip=={{ pip_ver }}
        - run: pip install poetry=={{ poetry_ver }}
        - run: pip install envo=={{ envo_ver }}
        - uses: gerbal/always-cache@v1.0.3
          id: root-venv-cache
          with:
            path: .venv
              tests/test_srvs/app_srv/.venv
              tests/test_srvs/django_srv/.venv
              tests/test_srvs/flask_srv/.venv
            {%- raw %}
            key: root-venv-v3-${{ hashFiles('poetry.lock') }}
            {%- endraw %}
            restore-keys: root-venv-v3-
        - name: Bootstrap repo
          run: envo ci run p.bootstrap
        """
        )

        ctx = {
            "pip_ver": self.pip_ver,
            "poetry_ver": self.poetry_ver,
            "envo_ver": self.envo_ver,
        }

        bootstrap_code = Template(bootstrap_code, undefined=StrictUndefined).render(
            **ctx
        )

        ctx = {
            "black_ver": self.black_ver,
            "python_versions": self.supported_versions,
            "bootstrap_code": bootstrap_code,
        }

        templ = Template(self.ci_template.read_text(), undefined=StrictUndefined)
        self.ci_out.write_text(templ.render(**ctx))

    @p.command
    def bootstrap(self) -> None:
        run("rm .venv -rf")
        path_before = os.environ["PATH"]
        os.environ[
            "PATH"
        ] = f"/home/kwazar/.pyenv/versions/{self.python_ver}/bin/:{os.environ['PATH']}"
        run(f"python -m venv .venv")
        os.environ["PATH"] = f"{self.python_ver}/bin/:{os.environ['PATH']}"
        super().bootstrap()

        os.environ["PATH"] = path_before


ThisEnv = EnviumLocalEnv
