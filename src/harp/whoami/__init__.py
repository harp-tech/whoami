"""The registry of WhoAmI identifiers reserved for Harp devices."""

from importlib import import_module
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from harp.whoami.registry import DEVICES, WhoAmI

__all__ = ["DEVICES", "App", "DeviceRecord", "DotnetToolApp", "WhoAmI"]

MODEL_CONFIG = ConfigDict(
    frozen=True,
    alias_generator=to_camel,
    validate_by_name=True,
    serialize_by_alias=True,
    use_attribute_docstrings=True,
)


class DotnetToolApp(BaseModel):
    """An app published as a .NET tool and resolved from nuget.org."""

    model_config = MODEL_CONFIG | ConfigDict(extra="forbid")

    type: Literal["dotnetTool"] = "dotnetTool"
    """The type of app."""

    package: Annotated[str, Field(pattern=r"^[A-Za-z0-9]+([._-][A-Za-z0-9]+)*$")]
    """The identifier of the package that provides the app."""


App: TypeAlias = Annotated[DotnetToolApp, Field(discriminator="type")]
"""The dedicated app for a device."""


class DeviceRecord(BaseModel):
    """The record of a device registered under its WhoAmI identifier."""

    model_config = MODEL_CONFIG

    whoami: int
    """The WhoAmI identifier of the device."""

    name: Annotated[str, Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")]
    """The name of the device."""

    authors: str | None = None
    """The authors of the device."""

    repository_url: str | None = None
    """The address of the source repository of the device."""

    project_url: str | None = None
    """The address of the home page of the device."""

    app: App | None = None
    """The dedicated app for this device."""


def __getattr__(name):
    if name in ("DEVICES", "WhoAmI"):
        return getattr(import_module("harp.whoami.registry"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
