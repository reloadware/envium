import os
import shutil
import sys
from pathlib import Path

from pytest import fixture


@fixture
def sandbox(request) -> Path:
    sandbox_dir = Path(request.module.__file__).parent / "sandbox"

    if sandbox_dir.exists():
        for f in sandbox_dir.glob("*"):
            if f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()

    sys.path.insert(0, str(sandbox_dir))

    if not sandbox_dir.exists():
        sandbox_dir.mkdir()

    (sandbox_dir / "__init__.py").touch()
    os.chdir(str(sandbox_dir))

    return sandbox_dir


@fixture
def env_sandbox() -> Path:
    environ_before = os.environ.copy()

    yield
    os.environ = environ_before
