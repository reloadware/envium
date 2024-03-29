import os
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

from pytest import raises

from tests import facade, utils
from tests.facade import Ctx, CtxGroup, computed_ctx_var, ctx_var


class TestMisc:
    def test_basic(self):
        class Context(Ctx):
            test_var: str = ctx_var()

        ctx = Context(name="ctx")
        ctx.test_var = "Cake"
        assert ctx.test_var == "Cake"

        ctx.validate()

    def test_shadowing(self):
        class BaseContext(Ctx):
            name: str = ctx_var()

        class Context(BaseContext):
            name: str = ctx_var("Cake")

        ctx = Context()
        assert ctx.name == "Cake"

        ctx.validate()

    def test_shadowing_optional(self):
        class BaseContext(Ctx):
            name: str = ctx_var()

        class Context(BaseContext):
            name: Optional[str] = ctx_var()

        ctx = Context()
        ctx.validate()

    def test_copy_from(self):
        class CakeCtx(Ctx):
            flavour: str = ctx_var()

        class CakeshopCtx(Ctx):
            class StorageCtx(CtxGroup):
                cake = CakeCtx()

            storage = StorageCtx()
            cake = CakeCtx()

        cakeshop_ctx = CakeshopCtx()
        cakeshop_ctx.storage.cake.flavour = "Caramel"

        cakeshop_ctx.cake.copy_from(cakeshop_ctx.storage.cake)

        assert cakeshop_ctx.cake.flavour == "Caramel"

        cakeshop_ctx.validate()

    def test_copy_from_default(self):
        class CakeCtx(Ctx):
            flavour: str = ctx_var("matcha")

        cake1 = CakeCtx()

        cake2 = CakeCtx()
        cake2.flavour = "wrong"

        cake2.copy_from(cake1)
        cake2.validate()

        assert cake2.flavour == "matcha"

    def test_groups_not_shared(self):
        class CakeshopCtx(Ctx):
            class CakeCtx(CtxGroup):
                flavour: str = ctx_var()

            cake = CakeCtx()

        cakeshop1_ctx = CakeshopCtx()
        cakeshop1_ctx.cake.flavour = "Caramel"

        cakeshop2_ctx = CakeshopCtx()
        cakeshop2_ctx.cake.flavour = "Matcha"

        cakeshop1_ctx.validate()
        cakeshop2_ctx.validate()

        assert cakeshop1_ctx.cake.flavour == "Caramel"
        assert cakeshop2_ctx.cake.flavour == "Matcha"

    def test_groups_not_shared_2(self):
        class CakeshopCtx(Ctx):
            class CakeCtx(CtxGroup):
                class FlavourCtx(CtxGroup):
                    name: str = ctx_var()

                flavour = FlavourCtx()

            cake = CakeCtx()

        cakeshop1_ctx = CakeshopCtx()
        cakeshop1_ctx.cake.flavour.name = "Caramel"

        cakeshop2_ctx = CakeshopCtx()
        cakeshop2_ctx.cake.flavour.name = "Matcha"

        cakeshop1_ctx.validate()
        cakeshop2_ctx.validate()

        assert cakeshop1_ctx.cake.flavour.name == "Caramel"
        assert cakeshop2_ctx.cake.flavour.name == "Matcha"

    def test_no_name(self):
        class Context(Ctx):
            test_var: str = ctx_var("Cake")

        ctx = Context()
        ctx.validate()

    def test_non_optional_default(self):
        class Context(Ctx):
            test_var: str = ctx_var(default="Cake")

        ctx = Context(name="ctx")
        assert ctx.test_var == "Cake"
        ctx.validate()

    def test_optional_no_value(self):
        class Context(Ctx):
            test_var: Optional[str] = ctx_var()

        ctx = Context()
        assert ctx.test_var is None

        ctx.validate()

    def test_optional_no_value_in_group(self):
        class Context(Ctx):
            class Group(CtxGroup):
                test_var: Optional[str] = ctx_var()

            group = Group()

        ctx = Context()
        assert ctx.group.test_var is None

        ctx.validate()

    def test_nested(self):
        class Context(Ctx):
            class Python(CtxGroup):
                version: str = ctx_var()
                name: str = ctx_var()

            test_var: str = ctx_var()
            python = Python()

        ctx = Context()
        ctx.python.version = "3.8.2"
        ctx.python.name = "python"
        ctx.test_var = "Cake"

        assert ctx.python.version == "3.8.2"
        assert ctx.python.name == "python"
        assert ctx.test_var == "Cake"

        ctx.validate()

    def test_double_nested(self):
        class Context(Ctx):
            class Python(CtxGroup):
                class Version(CtxGroup):
                    minor: str = ctx_var("3")
                    major: str = ctx_var("6")

                version = Version()
                name: str = ctx_var("python")

            test_var: str = ctx_var("Cake")
            python = Python()

        ctx = Context()
        assert ctx.python.version.minor == "3"
        assert ctx.python.version.major == "6"
        assert ctx.python.name == "python"
        assert ctx.test_var == "Cake"

        ctx.validate()

    def test_path(self):
        class Context(Ctx):
            test_var: Path = ctx_var(Path("my_path/child"))

        ctx = Context(name="ctx")

        assert ctx.test_var == Path("my_path/child")

        ctx.validate()

    def test_wrong_attr(self):
        class Context(Ctx):
            test_var: Path = ctx_var(Path("my_path/child"))

        ctx = Context(name="ctx")

        with raises(facade.UndefinedVarError):
            ctx.test_vars = 132

        ctx.validate()

    def test_default_factory(self):
        class Context(Ctx):
            test_var: List[str] = ctx_var(default_factory=lambda: ["1", "2"])

        ctx = Context(name="ctx")

        assert ctx.test_var == ["1", "2"]

        ctx.validate()


class TestComputed:
    def test_fget(self):
        class Context(Ctx):
            def fget(self) -> str:
                return "computed"

            test_var: str = facade.computed_ctx_var(fget=fget)

        ctx = Context(name="ctx")

        ctx.test_var = "computed"

        assert ctx.test_var == "computed"
        ctx.validate()

    def test_fset(self):
        class Context(Ctx):
            def fset(self, value) -> None:
                self.test_var._value = value * 2

            test_var: str = facade.computed_ctx_var(fset=fset)

        ctx = Context(name="ctx")

        ctx.test_var = "computed"

        assert ctx.test_var == "computedcomputed"
        ctx.validate()

    def test_error(self):
        class Context(Ctx):
            def fget(self) -> float:
                if self.cakes_n._value is None:
                    self.cakes_n._value = 2
                self.cakes_n._value -= 1
                return 1.0 / self.cakes_n._value

            cakes_n: float = facade.computed_ctx_var(fget=fget)

        ctx = Context(name="ctx")
        utils.assert_errors(
            ctx._errors,
            [
                facade.ComputedVarError(
                    "ctx.cakes_n", ZeroDivisionError("float division by zero")
                )
            ],
        )


class TestValidation:
    def test_non_optional_no_value(self):
        class Context(Ctx):
            test_var: str = ctx_var()

        ctx = Context(name="ctx")

        utils.assert_errors(ctx._errors, [facade.NoValueError("ctx.test_var", str)])

    def test_no_type(self):
        class Context(Ctx):
            test_var = ctx_var(default="Cake")

        ctx = Context(name="ctx")
        utils.assert_errors(ctx._errors, [facade.NoTypeError("ctx.test_var")])

    def test_wrong_type(self):
        class Context(Ctx):
            test_var: int = ctx_var(default="Cake")

        ctx = Context(name="ctx")
        utils.assert_errors(
            ctx._errors, [facade.WrongTypeError("ctx.test_var", int, str)]
        )

    def test_raises_validation_error(self):
        class Context(Ctx):
            test_var: int = ctx_var(default="Cake")

        ctx = Context(name="ctx")
        with raises(facade.ValidationErrors):
            ctx.validate()
