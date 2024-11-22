import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from envium import comp
from envium.exceptions import EnviumError, RedefinedVarError

if TYPE_CHECKING:
    pass

from envium.vars import ComputedMixin, FinalVar, Var, VarGroup, VarType

__all__ = ["env_var", "Environ", "computed_env_var", "EnvGroup"]


class EnvVar(Var):
    _name_override: Optional[str] = None
    _parent: "EnvGroup"

    def __init__(
        self,
        default: Optional[Any] = None,
        default_factory: Optional[Callable] = None,
        name_override: Optional[str] = None,
    ) -> None:
        super().__init__(default=default, default_factory=default_factory)
        self._name_override = name_override

    def _init_value(self) -> None:
        if self._parent._load:
            env_value = os.environ.get(self._get_env_name(), None)
            env_value = None if env_value == "None" else env_value
            self._value = self._from_str(env_value) if env_value else None

        if self._value is None:
            self._value = self._default

    def _get_env_name(self) -> str:
        if self._name_override:
            ret = self._name_override
        else:
            ret = self._fullname
            ret = ret.replace("_", "").replace(".", "_").replace("-", "")

        ret = ret.upper()

        return ret


class ComputedEnvVar(ComputedMixin, EnvVar):
    def __init__(
        self,
        fget: Optional[Callable] = None,
        fset: Optional[Callable] = None,
        name_override: Optional[str] = None,
    ) -> None:
        ComputedMixin.__init__(self, fget=fget, fset=fset)
        EnvVar.__init__(self, name_override=name_override)

    pass


class EnvGroup(VarGroup[EnvVar]):
    _name_override: Optional[str] = None
    _load: bool

    def __init__(
        self, name: Optional[str] = None, name_override: Optional[str] = None, load: bool = True
    ) -> None:
        super().__init__(name=name)
        self._load = load
        self._name_override = name_override

    @property
    def _fullname(self) -> str:
        if self._name_override:
            return self._name_override

        ret = super()._fullname
        return ret

    def _dump(self, path: Union[Path, str]) -> None:
        path = Path(path)

        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        path.touch(exist_ok=True)

        content = "\n".join(
            [f'{key}="{value}"' for key, value in self._root._get_env_vars().items()]
        )
        path.write_text(content, "utf-8")


class Environ(EnvGroup):
    def __init__(self, name: str, load: bool = False):
        if not name:
            raise EnviumError("Root needs to have a name")

        super().__init__(name=name, load=load)
        self._root = self
        self._process()

        if self._load:
            self._validate()

    def get_env_vars(self) -> Dict[str, str]:
        return self._get_env_vars()

    def validate(self) -> None:
        return self._validate()

    def dump(self, path: Union[Path, str]) -> None:
        return self._dump(path)

    def save_to_os_environ(self) -> None:
        os.environ.update(self.get_env_vars())

    def _get_env_vars(self) -> Dict[str, str]:
        """
        Return environmental variables in following format:
        {NAMESPACE_ENVNAME}

        :param owner_name:
        """

        self._validate()

        envs = {}
        for v in self._flat:
            name = v._get_env_name()
            value = v._get_value()
            if isinstance(value, list):
                envs[name] = comp.list_delimiter.join([str(v) for v in value])
            else:
                envs[name] = str(value)

        envs = {k.upper(): v for k, v in envs.items()}

        return envs

    @property
    def errors(self) -> List[EnviumError]:
        ret: List[EnviumError] = []
        env_names = []
        for v in self._flat:
            env_name = v._get_env_name()

            if env_name in env_names:
                ret.append(RedefinedVarError(env_name))

            env_names.append(env_name)

            ret.extend(v._get_errors())

        return ret


def env_var(
    default: Optional[Any] = None,
    name_override: Optional[str] = None,
    default_factory: Optional[Callable] = None,
) -> Any:
    return EnvVar(default=default, name_override=name_override, default_factory=default_factory)


def computed_env_var(
    fget: Optional[Callable] = None,
    fset: Optional[Callable] = None,
    name_override: Optional[str] = None,
) -> Any:
    return ComputedEnvVar(fget, fset, name_override)


Group = VarGroup
