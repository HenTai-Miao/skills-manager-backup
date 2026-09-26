"""Pipeline interfaces. Six Protocols, one ScoredItem dataclass.

Pattern inspired by xAI's open-sourced X For You algorithm (Apache 2.0).
Independent Python reimplementation.
"""
from typing import Protocol, TypeVar, Generic, runtime_checkable
from dataclasses import dataclass, field

Ctx = TypeVar("Ctx")
Item = TypeVar("Item")


@dataclass
class ScoredItem(Generic[Item]):
    item: Item
    score: float = 0.0
    components: dict[str, float] = field(default_factory=dict)


@runtime_checkable
class Source(Protocol[Ctx, Item]):
    name: str
    async def fetch(self, ctx: Ctx) -> list[Item]: ...


@runtime_checkable
class Hydrator(Protocol[Ctx, Item]):
    name: str
    async def hydrate(self, ctx: Ctx, items: list[Item]) -> None: ...


@runtime_checkable
class Filter(Protocol[Ctx, Item]):
    name: str
    def keep(self, ctx: Ctx, item: Item) -> bool: ...


@runtime_checkable
class Scorer(Protocol[Ctx, Item]):
    name: str
    async def score(self, ctx: Ctx, items: list[ScoredItem[Item]]) -> None: ...


@runtime_checkable
class Selector(Protocol[Ctx, Item]):
    name: str
    def select(self, ctx: Ctx, items: list[ScoredItem[Item]], k: int) -> list[ScoredItem[Item]]: ...


@runtime_checkable
class SideEffect(Protocol[Ctx, Item]):
    name: str
    async def emit(self, ctx: Ctx, items: list[ScoredItem[Item]]) -> None: ...
