import os
from pathlib import Path
from textwrap import dedent
from typing import Optional

from tests import facade, utils
from tests.facade import var, Environ, VarGroup
from pytest import raises


class TestMisc:
    def test_basic(self):
        class Env(Environ):
            test_var: str = facade.var()

        env = Env(name="env")

        env.test_var = "Cake"

        assert env.test_var == "Cake"
        assert env.get_env_vars() == {"ENV_TESTVAR": "Cake"}

    def test_raw(self):
        class Env(Environ):
            test_var: str = facade.var(raw=True)

        env = Env(name="env")

        env.test_var = "Cake"

        assert env.test_var == "Cake"
        assert env.get_env_vars() == {"TEST_VAR": "Cake"}

    def test_non_optional_default(self):
        class Env(Environ):
            test_var: str = facade.var(default="Cake")

        env = Env(name="env")
        assert env.test_var == "Cake"
        assert env.get_env_vars() == {"ENV_TESTVAR": "Cake"}

    def test_optional_no_value(self):
        class Env(Environ):
            test_var: Optional[str] = facade.var()

        env = Env(name="env")
        assert env.get_env_vars() == {"ENV_TESTVAR": "None"}

    def test_nested(self):
        class Env(Environ):
            class Python(VarGroup):
                version: str = var()
                name: str = var()

            test_var: str = var()
            python = Python()

        env = Env(name="env")
        env.python.version = "3.8.2"
        env.python.name = "python"
        env.test_var = "Cake"

        assert env.python.version == "3.8.2"
        assert env.python.name == "python"
        assert env.test_var == "Cake"

        assert env.get_env_vars() == {'ENV_PYTHON_NAME': 'python',
                                      'ENV_PYTHON_VERSION': '3.8.2',
                                      'ENV_TESTVAR': 'Cake'}

    def test_raw_in_nested(self):
        class Env(Environ):
            class Python(VarGroup):
                version: str = var(raw=True)
                name: str = var()

            test_var: str = var(raw=True)
            python = Python()

        env = Env(name="env")
        env.python.version = "3.8.2"
        env.python.name = "python"
        env.test_var = "Cake"

        assert env.python.version == "3.8.2"
        assert env.python.name == "python"
        assert env.test_var == "Cake"

        assert env.get_env_vars() == {'ENV_PYTHON_NAME': 'python',
                                      'VERSION': '3.8.2',
                                      'TEST_VAR': 'Cake'}

    def test_double_nested(self):
        class Env(Environ):
            class Python(VarGroup):
                class Version(VarGroup):
                    minor: str = var()
                    major: str = var()

                version = Version()
                name: str = var()

            test_var: str = var()
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

        assert env.get_env_vars() == {'ENV_PYTHON_NAME': 'python',
                                      'ENV_PYTHON_VERSION_MAJOR': '6',
                                      'ENV_PYTHON_VERSION_MINOR': '3',
                                      'ENV_TESTVAR': 'Cake'}

    def test_raw_group(self):
        class Env(Environ):
            class Python(VarGroup):
                version: str = var()
                name: str = var()

            python = Python(raw=True)

        env = Env(name="env")
        env.python.version = "3.8.2"
        env.python.name = "python"
        env.test_var = "Cake"

        assert env.python.version == "3.8.2"
        assert env.python.name == "python"

        assert env.get_env_vars() == {'PYTHON_NAME': 'python',
                                      'PYTHON_VERSION': '3.8.2'}

    def test_raw_nested_group(self):
        class Env(Environ):
            class Python(VarGroup):
                class Version(VarGroup):
                    minor: str = var()
                    major: str = var()

                version = Version(raw=True)
                name: str = var()

            python = Python()

        env = Env(name="env")
        env.python.version.minor = "3"
        env.python.version.major = "6"
        env.python.name = "python"

        assert env.python.version.minor == "3"
        assert env.python.version.major == "6"
        assert env.python.name == "python"

        assert env.get_env_vars() == {'ENV_PYTHON_NAME': 'python',
                                      'VERSION_MAJOR': '6',
                                      'VERSION_MINOR': '3'}


class TestComputed:
    def test_fget(self):
        class Env(Environ):
            def fget(self) -> str:
                return "computed"
            test_var: str = facade.computed_var(fget=fget)

        env = Env(name="env")

        env.test_var = "computed"

        assert env.test_var == "computed"
        assert env.get_env_vars() == {"ENV_TESTVAR": "computed"}

    def test_fset(self):
        class Env(Environ):
            def fset(self, value) -> None:
                self.test_var._value = value * 2

            test_var: str = facade.computed_var(fset=fset)

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
            cakes_n: float = facade.computed_var(fget=fget)

        env = Env(name="env")
        utils.assert_errors(env.errors, [facade.ComputedVarError("env.cakes_n", ZeroDivisionError("float division by zero"))])


class TestLoading:
    def test_basic(self, sandbox, env_sandbox):
        class Env(Environ):
            class Python(VarGroup):
                class Version(VarGroup):
                    minor: str = var(default="6")
                    major: str = var(default="3")

                version = Version()
                name: str = var(default="Python")

            test_var: str = var(raw=True, default="test_var")
            python = Python()

        os.environ["ENV_PYTHON_VERSION_MINOR"] = "8"
        os.environ["TEST_VAR"] = "From environ"
        env = Env(name="env", load=True)
        assert env.get_env_vars() == {'ENV_PYTHON_NAME': 'Python',
                                      'ENV_PYTHON_VERSION_MAJOR': '3',
                                      'ENV_PYTHON_VERSION_MINOR': '8',
                                      'TEST_VAR': 'From environ'}


class TestDumping:
    def test_basic(self, sandbox):
        class Env(Environ):
            class Python(VarGroup):
                class Version(VarGroup):
                    minor: str = var(default="6")
                    major: str = var(default="3")

                version = Version()
                name: str = var(default="Python")

            test_var: str = var(default="test_var")
            python = Python()

        env = Env(name="env")
        env_path = Path("envs/.env")
        env.dump(env_path)

        assert env_path.read_text() == dedent(
            """
            ENV_PYTHON_NAME="Python"
            ENV_PYTHON_VERSION_MAJOR="3"
            ENV_PYTHON_VERSION_MINOR="6"
            ENV_TESTVAR="test_var"
            """
        ).strip()


class TestValidation:
    def test_non_optional_no_value(self):
        class Env(Environ):
            test_var: str = facade.var()

        env = Env(name="env")

        utils.assert_errors(env.errors, [facade.NoValueError("env.test_var", str)])

    def test_no_type(self):
        class Env(Environ):
            test_var = facade.var(default="Cake")

        env = Env(name="env")
        utils.assert_errors(env.errors, [facade.NoTypeError("env.test_var")])

    def test_wrong_type(self):
        class Env(Environ):
            test_var: int = facade.var(default="Cake")

        env = Env(name="env")
        utils.assert_errors(env.errors, [facade.WrongTypeError("env.test_var", int, str)])

    def test_raises_validation_error(self):
        class Env(Environ):
            test_var: int = facade.var(default="Cake")

        env = Env(name="env")
        with raises(facade.ValidationErrors):
            env.validate()

    def test_redefined_var(self):
        class Env(Environ):
            class Python(VarGroup):
                name: str = var(raw=True, default="Python")

            python = Python()
            name: str = var(raw=True, default="MyEnv")

        env = Env(name="env")
        assert env.python.name == "Python"
        assert env.name == "MyEnv"

        utils.assert_errors(env.errors, [facade.RedefinedVarError("NAME")])
