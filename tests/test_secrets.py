import os
from pathlib import Path
from textwrap import dedent
from typing import Optional

from pytest import raises

from tests import facade, utils
from tests.facade import Secrets, SecretsGroup, computed_secret, secret


class TestMisc:
    def test_basic(self, mock_getpass):
        class Secr(Secrets):
            password: str = secret()

        mock_getpass.append("SecretPassword")
        secr = Secr(name="secr")
        assert secr.password == "SecretPassword"

        secr.validate()

    def test_no_name(self):
        class Secr(Secrets):
            test_var: str = secret("Cake")

        secr = Secr()
        secr.validate()

    def test_non_optional_default(self):
        class Secr(Secrets):
            test_var: str = secret(default="Cake")

        secr = Secr(name="secr")
        assert secr.test_var == "Cake"
        secr.validate()

    def test_optional_no_value(self):
        class Secr(Secrets):
            test_var: Optional[str] = secret(None, value_from_input=False)

        secr = Secr()
        assert secr.test_var is None

        secr.validate()

    def test_optional_no_value_in_group(self):
        class Secr(Secrets):
            class Group(SecretsGroup):
                test_var: Optional[str] = secret(None, value_from_input=False)

            group = Group()

        secr = Secr()
        assert secr.group.test_var is None

        secr.validate()

    def test_nested(self, mock_getpass):
        class Secr(Secrets):
            class Python(SecretsGroup):
                password: str = secret()

            main_password: str = secret()
            python = Python()

        mock_getpass.append("main_pass")
        mock_getpass.append("python_pass")

        secr = Secr()

        assert secr.python.password == "python_pass"
        assert secr.main_password == "main_pass"

        secr.validate()

    def test_double_nested(self, mock_getpass):
        class Secr(Secrets):
            class Python(SecretsGroup):
                class Version(SecretsGroup):
                    minor: str = secret()

                version = Version()
                name: str = secret()

            test_pass: str = secret("default_password")
            python = Python()

        mock_getpass.append("name_secret")
        mock_getpass.append("minor_secret")

        secr = Secr()
        assert secr.python.version.minor == "minor_secret"
        assert secr.python.name == "name_secret"
        assert secr.test_pass == "default_password"

        secr.validate()

    def test_path(self, mock_getpass):
        class Secr(Secrets):
            test_secr: Path = secret()

        mock_getpass.append("/secret/path")
        secr = Secr()

        assert secr.test_secr == Path("/secret/path")

        secr.validate()


class TestComputed:
    def test_fget(self, mock_getpass):
        class Secr(Secrets):
            def fget(self) -> str:
                if self.test_pass._value:
                    return self.test_pass._value * 2
                else:
                    return self.test_pass._value

            test_pass: str = computed_secret(fget=fget)

        mock_getpass.append("Cake")

        secr = Secr()

        assert secr.test_pass == "CakeCake"
        secr.validate()

    def test_fset(self, mock_getpass):
        class Secr(Secrets):
            def fset(self, value) -> None:
                self.test_pass._value = value * 2

            test_pass: str = computed_secret(fset=fset)

        mock_getpass.append("Cake")
        secr = Secr()

        assert secr.test_pass == "CakeCake"
        secr.validate()

    def test_error(self, mock_getpass):
        class Secr(Secrets):
            def fget(self) -> float:
                if self.cakes_n._value is None:
                    return self.cakes_n._value
                return 1.0 / 0

            cakes_n: int = computed_secret(fget=fget)

        mock_getpass.append(1)
        secr = Secr()
        utils.assert_errors(
            secr._errors,
            [
                facade.ComputedVarError(
                    ".cakes_n", ZeroDivisionError("float division by zero")
                )
            ],
        )


class TestValidation:
    def test_non_optional_no_value(self, mock_getpass):
        class Secr(Secrets):
            test_var: str = secret(None, value_from_input=False)

        secr = Secr(name="secr")

        utils.assert_errors(secr._errors, [facade.NoValueError("secr.test_var", str)])

    def test_no_type(self):
        class Secr(Secrets):
            test_var = secret(default="Cake")

        secr = Secr(name="secr")
        utils.assert_errors(secr._errors, [facade.NoTypeError("secr.test_var")])

    def test_wrong_type(self):
        class Secr(Secrets):
            test_var: int = secret(default="Cake")

        secr = Secr(name="secr")
        utils.assert_errors(
            secr._errors, [facade.WrongTypeError("secr.test_var", int, str)]
        )

    def test_raises_validation_error(self):
        class Secr(Secrets):
            test_var: int = secret(default="Cake")

        secr = Secr(name="secr")
        with raises(facade.ValidationErrors):
            secr.validate()
