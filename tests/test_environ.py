import os
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

from pytest import raises

from tests import facade, utils
from tests.facade import EnvGroup, Environ, env_var


class TestMisc:
    def test_basic(self):
        class Env(Environ):
            test_var: str = env_var()

        env = Env(name="env")

        env.test_var = "Cake"

        assert env.test_var == "Cake"
        assert env.get_env_vars() == {"ENV_TESTVAR": "Cake"}

    def test_no_name(self):
        class Env(Environ):
            test_var: str = env_var()

        with raises(facade.EnviumError):
            env = Env(name="")

    def test_raw(self):
        class Env(Environ):
            test_var: str = env_var(raw=True)

        env = Env(name="env")

        env.test_var = "Cake"

        assert env.test_var == "Cake"
        assert env.get_env_vars() == {"TEST_VAR": "Cake"}

    def test_non_optional_default(self):
        class Env(Environ):
            test_var: str = env_var(default="Cake")

        env = Env(name="env")
        assert env.test_var == "Cake"
        assert env.get_env_vars() == {"ENV_TESTVAR": "Cake"}

    def test_non_optional_set(self):
        class Env(Environ):
            test_var: str = env_var()

        env = Env(name="env")
        env.test_var = "Cake"
        assert env.test_var == "Cake"
        assert env.get_env_vars() == {"ENV_TESTVAR": "Cake"}

    def test_optional_no_value(self):
        class Env(Environ):
            test_var: Optional[str] = env_var()

        env = Env(name="env")
        assert env.get_env_vars() == {"ENV_TESTVAR": "None"}

    def test_optional_no_value_in_group(self):
        class Env(Environ):
            class Group(EnvGroup):
                test_var: Optional[str] = env_var()

            group = Group()

        env = Env(name="env")
        assert env.get_env_vars() == {"ENV_GROUP_TESTVAR": "None"}

    def test_nested(self):
        class Env(Environ):
            class Python(EnvGroup):
                version: str = env_var()
                name: str = env_var()

            test_var: str = env_var()
            python = Python()

        env = Env(name="env")
        env.python.version = "3.8.2"
        env.python.name = "python"
        env.test_var = "Cake"

        assert env.python.version == "3.8.2"
        assert env.python.name == "python"
        assert env.test_var == "Cake"

        assert env.get_env_vars() == {
            "ENV_PYTHON_NAME": "python",
            "ENV_PYTHON_VERSION": "3.8.2",
            "ENV_TESTVAR": "Cake",
        }

    def test_raw_in_nested(self):
        class Env(Environ):
            class Python(EnvGroup):
                version: str = env_var(raw=True)
                name: str = env_var()

            test_var: str = env_var(raw=True)
            python = Python()

        env = Env(name="env")
        env.python.version = "3.8.2"
        env.python.name = "python"
        env.test_var = "Cake"

        assert env.python.version == "3.8.2"
        assert env.python.name == "python"
        assert env.test_var == "Cake"

        assert env.get_env_vars() == {
            "ENV_PYTHON_NAME": "python",
            "VERSION": "3.8.2",
            "TEST_VAR": "Cake",
        }

    def test_double_nested(self):
        class Env(Environ):
            class Python(EnvGroup):
                class Version(EnvGroup):
                    minor: str = env_var()
                    major: str = env_var()

                version = Version()
                name: str = env_var()

            test_var: str = env_var()
            python = Python()

        env = Env(name="env")
        env.python.version.minor = "3"
        env.python.version.major = "6"
        env.python.name = "python"
        env.test_var = "Cake"

        assert env.python.version.minor == "3"
        assert env.python.version.major == "6"
        assert env.python.name == "python"
        assert env.test_var == "Cake"

        assert env.get_env_vars() == {
            "ENV_PYTHON_NAME": "python",
            "ENV_PYTHON_VERSION_MAJOR": "6",
            "ENV_PYTHON_VERSION_MINOR": "3",
            "ENV_TESTVAR": "Cake",
        }

    def test_raw_group(self):
        class Env(Environ):
            class Python(EnvGroup):
                version: str = env_var()
                name: str = env_var()

            python = Python(raw=True)

        env = Env(name="env")
        env.python.version = "3.8.2"
        env.python.name = "python"

        assert env.python.version == "3.8.2"
        assert env.python.name == "python"

        assert env.get_env_vars() == {
            "PYTHON_NAME": "python",
            "PYTHON_VERSION": "3.8.2",
        }

    def test_raw_nested_group(self):
        class Env(Environ):
            class Python(EnvGroup):
                class Version(EnvGroup):
                    minor: str = env_var()
                    major: str = env_var()

                version = Version(raw=True)
                name: str = env_var()

            python = Python()

        env = Env(name="env")
        env.python.version.minor = "3"
        env.python.version.major = "6"
        env.python.name = "python"

        assert env.python.version.minor == "3"
        assert env.python.version.major == "6"
        assert env.python.name == "python"

        assert env.get_env_vars() == {
            "ENV_PYTHON_NAME": "python",
            "VERSION_MAJOR": "6",
            "VERSION_MINOR": "3",
        }

    def test_path(self):
        class Env(Environ):
            test_var: Path = env_var(Path("my_path/child"))

        env = Env(name="env")

        assert env.test_var == Path("my_path/child")
        assert env.get_env_vars() == {"ENV_TESTVAR": "my_path/child"}

    def test_default_factory(self):
        class Env(Environ):
            test_var: List[str] = env_var(default_factory=lambda: ["1", "2"])

        env = Env(name="ctx")

        assert env.test_var == ["1", "2"]
        env.validate()

    def test_list(self):
        class Env(Environ):
            test_var: List[str] = env_var()
            test_path: List[Path] = env_var()

        env = Env(name="env")

        env.test_var = ["1", "2"]
        env.test_path = [Path("home/user"), Path("home/user2")]
        assert env.get_env_vars() == {
            "ENV_TESTVAR": "1:2",
            "ENV_TESTPATH": "home/user:home/user2",
        }

    def test_hyphen_in_env_name(self):
        class Env(Environ):
            test_var: List[str] = env_var()

        env = Env(name="my-env")

        env.test_var = "Cake"
        assert env.get_env_vars() == {
            "MYENV_TESTVAR": "Cake",
        }

    def test_no_value(self):
        class Env(Environ):
            test_var: List[str] = env_var()
            test_path: List[Path] = env_var()

        env = Env(name="env")

        env.test_var = "Cake"
        with raises(expected_exception=facade.ValidationErrors) as e:
            env.get_env_vars()

        assert len(e.value.errors) == 1
        assert isinstance(e.value.errors[0], facade.NoValueError)
        assert (
            e.value.errors[0].args[0]
            == 'Expected value of type "typing.List[pathlib.Path]" for var "env.test_path" not None'
        )


class TestComputed:
    def test_fget(self):
        class Env(Environ):
            def fget(self) -> str:
                return "computed"

            test_var: str = facade.computed_env_var(fget=fget)

        env = Env(name="env")

        env.test_var = "computed"

        assert env.test_var == "computed"
        assert env.get_env_vars() == {"ENV_TESTVAR": "computed"}

    def test_fset(self):
        class Env(Environ):
            def fset(self, value) -> None:
                self.test_var._value = value * 2

            test_var: str = facade.computed_env_var(fset=fset)

        env = Env(name="env")

        env.test_var = "computed"

        assert env.test_var == "computedcomputed"
        assert env.get_env_vars() == {"ENV_TESTVAR": "computedcomputed"}

    def test_error(self):
        class Env(Environ):
            def fget(self) -> float:
                if self.cakes_n._value is None:
                    self.cakes_n._value = 2
                self.cakes_n._value -= 1
                return 1.0 / self.cakes_n._value

            cakes_n: float = facade.computed_env_var(fget=fget)

        env = Env(name="env")
        utils.assert_errors(
            env._errors,
            [
                facade.ComputedVarError(
                    "env.cakes_n", ZeroDivisionError("float division by zero")
                )
            ],
        )


class TestLoading:
    def test_basic(self, sandbox, env_sandbox):
        class Env(Environ):
            class Python(EnvGroup):
                class Version(EnvGroup):
                    minor: str = env_var("6")
                    major: str = env_var(default="3")

                version = Version()
                name: str = env_var(default="Python")

            test_var: str = env_var(raw=True, default="test_var")
            python = Python()

        os.environ["ENV_PYTHON_VERSION_MINOR"] = "8"
        os.environ["TEST_VAR"] = "From environ"
        env = Env(name="env", load=True)
        assert env.get_env_vars() == {
            "ENV_PYTHON_NAME": "Python",
            "ENV_PYTHON_VERSION_MAJOR": "3",
            "ENV_PYTHON_VERSION_MINOR": "8",
            "TEST_VAR": "From environ",
        }

    def test_path(self, sandbox, env_sandbox):
        class Env(Environ):
            test_var: Path = env_var()

        os.environ["ENV_TESTVAR"] = "test_path/child"

        env = Env(name="env", load=True)
        assert env.test_var == Path("test_path/child")

    def test_non_optional(self, sandbox, env_sandbox):
        class Env(Environ):
            test_var: Path = env_var()

        with raises(facade.ValidationErrors):
            env = Env(name="env", load=True)

    def test_bool(self, sandbox, env_sandbox):
        os.environ["ENV_TESTVAR"] = "False"

        class Env(Environ):
            test_var: bool = env_var(default=True)

        env = Env(name="env", load=True)
        assert env.test_var is False

    def test_str(self, sandbox, env_sandbox):
        os.environ["ENV_DEFAULTCAKE"] = "Crepe"

        class Env(Environ):
            default_cake: str = env_var()

        env = Env(name="env", load=True)
        assert env.default_cake == "Crepe"

    def test_optional_no_value(self, env_sandbox):
        os.environ["ENV_TESTVAR"] = "None"

        class Env(Environ):
            test_var: Optional[str] = env_var()

        env = Env(name="env", load=True)
        assert env.test_var is None
        assert env.get_env_vars() == {"ENV_TESTVAR": "None"}

    def test_list(self):
        os.environ["ENV_TESTVAR"] = "first:second"

        class Env(Environ):
            test_var: List[str] = env_var()

        env = Env(name="env", load=True)

        assert env.test_var == ["first", "second"]


class TestDumping:
    def test_basic(self, sandbox):
        class Env(Environ):
            class Python(EnvGroup):
                class Version(EnvGroup):
                    minor: str = env_var(default="6")
                    major: str = env_var(default="3")

                version = Version()
                name: str = env_var(default="Python")

            test_var: str = env_var(default="test_var")
            python = Python()

        env = Env(name="env")
        env_path = Path("envs/.env")
        env.dump(env_path)

        assert (
            env_path.read_text()
            == dedent(
                """
        ENV_PYTHON_NAME="Python"
        ENV_PYTHON_VERSION_MAJOR="3"
        ENV_PYTHON_VERSION_MINOR="6"
        ENV_TESTVAR="test_var"
        """
            ).strip()
        )


class TestValidation:
    def test_non_optional_no_value(self):
        class Env(Environ):
            test_var: str = env_var()

        env = Env(name="env")

        utils.assert_errors(env._errors, [facade.NoValueError("env.test_var", str)])

    def test_no_type(self):
        class Env(Environ):
            test_var = env_var(default="Cake")

        env = Env(name="env")
        utils.assert_errors(env._errors, [facade.NoTypeError("env.test_var")])

    def test_wrong_type(self):
        class Env(Environ):
            test_var: int = env_var(default="Cake")

        env = Env(name="env")
        utils.assert_errors(
            env._errors, [facade.WrongTypeError("env.test_var", int, str)]
        )

    def test_raises_validation_error(self):
        class Env(Environ):
            test_var: int = env_var(default="Cake")

        env = Env(name="env")
        with raises(facade.ValidationErrors):
            env.validate()

    def env_var(self):
        class Env(Environ):
            class Python(EnvGroup):
                name: str = env_var(raw=True, default="Python")

            python = Python()
            name: str = env_var(raw=True, default="MyEnv")

        env = Env(name="env")
        assert env.python.name == "Python"
        assert env.name == "MyEnv"

        utils.assert_errors(env._errors, [facade.RedefinedVarError("NAME")])
