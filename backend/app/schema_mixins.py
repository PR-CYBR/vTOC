"""Reusable mixins and helpers for Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Optional, Type

from pydantic import BaseModel, ConfigDict


class ORMModelMixin(BaseModel):
    """Mixin enabling ORM mode for read schemas."""

    model_config = ConfigDict(from_attributes=True)


class IdentifierMixin(BaseModel):
    """Adds an integer identifier field."""

    id: int


class TimestampsMixin(BaseModel):
    """Adds created/updated timestamp fields."""

    created_at: datetime
    updated_at: datetime


class SlugNameMixin(BaseModel):
    """Common slug/name fields shared across schemas."""

    slug: str
    name: str


class DescriptionMixin(BaseModel):
    """Optional description field."""

    description: Optional[str] = None


class ActivationFields(BaseModel):
    """Boolean activation flag shared by multiple models."""

    is_active: bool = True


def create_partial_model(
    name: str,
    base: Type[BaseModel],
    *,
    exclude: Iterable[str] | None = None,
    additional_fields: dict[str, tuple[Any, Any]] | None = None,
) -> type[BaseModel]:
    """Build a partial/patch model from ``base`` where every field is optional."""

    exclude_set = set(exclude or [])
    annotations: dict[str, Any] = {}
    namespace: dict[str, Any] = {"__module__": base.__module__}
    for field_name, field_info in base.model_fields.items():
        if field_name in exclude_set:
            continue
        annotation = field_info.annotation or Any
        annotations[field_name] = Optional[annotation]
        namespace[field_name] = None
    if additional_fields:
        for field_name, (annotation, default) in additional_fields.items():
            annotations[field_name] = annotation
            namespace[field_name] = default
    namespace["__annotations__"] = annotations
    return type(name, (BaseModel,), namespace)
