from pathlib import Path

this_dir = Path(__file__).parent.absolute()
import envium


def assert_mypy_in_file(file: Path) -> None:
    from mypy import build
    from mypy.fscache import FileSystemCache
    from mypy.main import process_options

    fscache = FileSystemCache()
    sources, options = process_options([str(file)], fscache=fscache)
    options.strict_optional = False
    options.fine_grained_incremental = True
    options.check_untyped_defs = True
    options.mypy_path = [str(Path(envium.__file__).parent.parent)]

    res = build.build(sources, options, None, None, fscache)
    assert res.errors == []


def test_environ():
    assert_mypy_in_file(this_dir / "environ_test.py_")


def test_ctx():
    assert_mypy_in_file(this_dir / "ctx_test.py_")


def test_secrets():
    assert_mypy_in_file(this_dir / "secrets_test.py_")
