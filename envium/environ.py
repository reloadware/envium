import inspect
import os
from abc import ABC, abstractmethod
from copy import deepcopy

from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union, ClassVar
)

# Python >= 3.8
import typing


try:
    typing.get_args
    typing.get_origin
# Compatibility
except AttributeError:
    typing.get_args = lambda t: getattr(t, '__args__', ()) if t is not Generic else Generic
    typing.get_origin = lambda t: getattr(t, '__origin__', None)


if TYPE_CHECKING:
    from envo.env import BaseEnv



__all__ = [
    "var",
    "computed_var",
    "VarGroup",
    "Environ"
]


class EnviumError(Exception):
    pass


class RedefinedVarError(EnviumError):
    def __init__(self, var_name: str) -> None:
        msg = f'Variable "{var_name}" is redefined'
        super().__init__(msg)


class WrongTypeError(EnviumError):
    def __init__(self, var_name: str, type_: Type, got_type: Type) -> None:
        msg = f'Expected type "{type_.__name__}" for var "{var_name}" got "{got_type}"'
        super().__init__(msg)


class NoTypeError(EnviumError):
    def __init__(self, var_name: str) -> None:
        msg = f'Type annotation for var "{var_name}" is missing'
        super().__init__(msg)


class NoValueError(EnviumError):
    def __init__(self, var_name: str, type_: Type) -> None:
        msg = f'Expected value of type "{type_.__name__}" for var "{var_name}" not None'
        super().__init__(msg)


class ComputedVarError(EnviumError):
    def __init__(self, var_name: str, exception: Exception) -> None:
        msg = f'During computing "{var_name}" following error occured: \n{repr(exception)}'
        super().__init__(msg)


class ValidationErrors(EnviumError):
    errors: List[EnviumError]

    def __init__(self, errors: List[EnviumError]) -> None:
        self.errors = errors
        msg = "\n".join(repr(e) for e in self.errors)
        super().__init__(msg)


VarType = Type["VarType"]


class BaseVar(ABC):
    _raw: bool = False
    e: Optional["VarGroup"]
    _parent: Optional["BaseVar"]
    _name: Optional[str]

    def __init__(self, raw: bool = False) -> None:
        self._raw = raw
        self.e = None
        self._parent = None
        self._name = None

    @property
    def _fullname(self) -> str:
        if self._raw:
            return self._name

        ret = f"{self._parent._fullname}.{self._name}" if self._parent else f"{self.e._name}.{self._name}"
        return ret


class FinalVar(BaseVar, ABC):
    _type_: Optional[Type]
    _optional: bool
    _vars: List["BaseVar"]
    _value: Optional[VarType]

    _final: ClassVar[bool] = True
    _ready: bool

    def __init__(self, raw: bool = False) -> None:
        super().__init__(raw=raw)

        self._type_ = None
        self._optional = False
        self._vars = []
        self._value = None
        self._ready = False

    @abstractmethod
    def _init_value(self, from_environ: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    def _get_errors(self) -> List[EnviumError]:
        return []

    def _get_env_name(self) -> str:
        if self._raw:
            ret = self._name
        else:
            ret = self._fullname
            ret = ret.replace("_", "").replace(".", "_")

        ret = ret.upper()

        return ret

    def __repr__(self) -> str:
        return f"{self._fullname}"

    @abstractmethod
    def _get_value(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _set_value(self, new_value) -> None:
        raise NotImplementedError


class Var(FinalVar):
    _default: Optional[VarType]
    _default_factory: Optional[Callable]

    def __init__(self, raw: bool = False,
                 default: Optional[VarType] = None,
                 default_factory: Optional[Callable] = None) -> None:
        super().__init__(raw=raw)
        self._default_factory = default_factory
        self._default = default

        if self._default_factory:
            self._default = self._default_factory()

    def _init_value(self, from_environ: bool):
        if from_environ:
            self._value = os.environ.get(self._get_env_name(), None)

        if not self._value:
            self._value = self._default

    def _get_value(self) -> Any:
        return self._value

    def _set_value(self, new_value) -> None:
        self._value = new_value

    def _get_errors(self) -> List[EnviumError]:
        ret = []

        # Try evaluating value first. There might be some issues with that
        if not self._type_:
            return [NoTypeError(var_name=self._fullname)]

        if not self._optional and self._get_value() is None:
            ret.append(NoValueError(type_=self._type_, var_name=self._fullname))
        elif self._get_value() is not None:
            try:
                if self._type_ and not isinstance(self._get_value(), self._type_):
                    ret.append(
                        WrongTypeError(type_=self._type_, var_name=self._fullname, got_type=type(self._get_value())))
            except TypeError:
                # isinstance will fail for types like Union[] etc
                pass

        return super()._get_errors() + ret


class ComputedVar(FinalVar):
    _fget: Optional[Callable]
    _fset: Optional[Callable]

    def __init__(self, fget: Optional[Callable] = None, fset: Optional[Callable] = None, raw: bool = False) -> None:
        super().__init__(raw=raw)
        self._fget = fget
        self._fset = fset

    def _init_value(self, from_environ: bool):
        self._value = self._get_value()

    def _get_value(self) -> Any:
        object.__setattr__(self, "_ready", False)
        if self._fget:
            ret = self._fget(self.e)
        else:
            ret = self._value
        object.__setattr__(self, "_ready", True)
        return ret

    def _set_value(self, new_value) -> None:
        object.__setattr__(self, "_ready", False)
        if self._fset:
            self._fset(self.e, new_value)
        else:
            self._value = new_value
        object.__setattr__(self, "_ready", True)

    def _get_errors(self) -> List[EnviumError]:
        try:
            self._get_value()
        except Exception as e:
            return [ComputedVarError(var_name=self._fullname, exception=e)]

        return super()._get_errors()


class VarGroup(BaseVar):
    children: List[BaseVar]

    _load: bool

    def __init__(self, raw: bool = False, name: Optional[str] = None, load: bool=True):
        super().__init__(raw=raw)
        self.children = []
        self._load = load
        self._name = name

        # Create copy of the var class attributes and assign them to the instance
        for f in dir(self):
            attr = inspect.getattr_static(self, f)

            if isinstance(attr, BaseVar):
                setattr(self, f, deepcopy(attr))

    def process(self, e: "VarGroup") -> None:
        self.e = e

        annotations = [c.__annotations__ for c in self.__class__.__mro__ if hasattr(c, "__annotations__")]
        flat_annotations = {}

        for a in annotations:
            flat_annotations.update(a)

        for n in dir(self):
            v = inspect.getattr_static(self, n)

            if v is self.e:
                continue

            if v is self._parent:
                continue

            if not isinstance(v, BaseVar):
                continue

            type_ = flat_annotations.get(n, None)
            optional = typing.get_origin(type_) is Union and type(None) in typing.get_args(type_)
            v._type_ = type_
            v._name = n
            v._optional = optional
            v.e = self.e
            v._parent = self

            self.children.append(v)

            if isinstance(v, VarGroup):
                v.process(self.e)
            elif isinstance(v, FinalVar):
                v._init_value(from_environ=self._load)


            v._ready = True

    @property
    def flat(self) -> List[FinalVar]:
        ret = []
        for c in self.children:
            if isinstance(c, VarGroup):
                ret.extend(c.flat)
            else:
                ret.append(c)

        ret = sorted(ret, key=lambda x: x._fullname)

        return ret

    def __setattr__(self, key: str, value: Any) -> None:
        if not hasattr(self, key):
            object.__setattr__(self, key, value)
            return

        attr = object.__getattribute__(self, key)

        if not isinstance(attr, FinalVar):
            object.__setattr__(self, key, value)
            return

        if not attr._ready:
            object.__setattr__(self, key, value)
            return

        attr._set_value(value)

    def __getattribute__(self, item: str) -> Any:
        attr = object.__getattribute__(self, item)

        if not isinstance(attr, FinalVar):
            return attr

        if not attr._ready:
            return attr

        return attr._get_value()

    @property
    def errors(self) -> List[EnviumError]:
        ret = []
        env_names = []
        for v in self.flat:
            env_name = v._get_env_name()

            if env_name in env_names:
                ret.append(RedefinedVarError(env_name))

            env_names.append(env_name)

            ret.extend(v._get_errors())

        return ret

    def get_env_vars(self) -> Dict[str, str]:
        """
        Return environmental variables in following format:
        {NAMESPACE_ENVNAME}

        :param owner_name:
        """

        self.validate()

        envs = {}
        for v in self.flat:
            name = v._get_env_name()
            envs[name] = str(v._get_value())

        envs = {k.upper(): v for k, v in envs.items()}

        return envs

    def validate(self) -> None:
        errors = self.errors

        if errors:
            raise ValidationErrors(errors)

    def dump(self, path: Union[Path, str]) -> None:
        path = Path(path)

        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        path.touch(exist_ok=True)

        content = "\n".join(
            [f'{key}="{value}"' for key, value in self.e.get_env_vars().items()]
        )
        path.write_text(content, "utf-8")


class Environ(VarGroup):
    def __init__(self, name: Optional[str] = None, load: bool=True):
        super().__init__(raw=True, name=name, load=load)
        self.process(self)


var = Var
computed_var = ComputedVar
Group = VarGroup
