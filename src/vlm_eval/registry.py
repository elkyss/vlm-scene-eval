"""Minimal name -> class registry so components can be selected from config."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._items: dict[str, Callable[..., T]] = {}

    def register(self, name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
        def decorator(factory: Callable[..., T]) -> Callable[..., T]:
            if name in self._items:
                raise ValueError(f"{self.kind} '{name}' is already registered")
            self._items[name] = factory
            return factory

        return decorator

    def build(self, name: str, **params: Any) -> T:
        if name not in self._items:
            raise KeyError(f"Unknown {self.kind} '{name}'. Available: {sorted(self._items)}")
        return self._items[name](**params)

    def names(self) -> list[str]:
        return sorted(self._items)
