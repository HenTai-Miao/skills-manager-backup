"""Pipeline runner: executes the six stages."""
import asyncio
import logging
from typing import Generic, TypeVar

from .interfaces import (
    Source, Hydrator, Filter, Scorer, Selector, SideEffect, ScoredItem,
)

Ctx = TypeVar("Ctx")
Item = TypeVar("Item")

log = logging.getLogger(__name__)


class Pipeline(Generic[Ctx, Item]):
    def __init__(
        self,
        sources: list[Source[Ctx, Item]],
        hydrators: list[Hydrator[Ctx, Item]],
        filters: list[Filter[Ctx, Item]],
        scorers: list[Scorer[Ctx, Item]],
        selector: Selector[Ctx, Item],
        side_effects: list[SideEffect[Ctx, Item]],
    ):
        self.sources = sources
        self.hydrators = hydrators
        self.filters = filters
        self.scorers = scorers
        self.selector = selector
        self.side_effects = side_effects

    async def run(self, ctx: Ctx, k: int) -> list[ScoredItem[Item]]:
        # 1. Sources parallel
        source_results = await asyncio.gather(
            *[self._safe_fetch(s, ctx) for s in self.sources]
        )
        items: list[Item] = [it for batch in source_results for it in batch]

        # 2. Hydrators parallel
        await asyncio.gather(
            *[self._safe_hydrate(h, ctx, items) for h in self.hydrators]
        )

        # 3. Filters sequential
        for f in self.filters:
            items = [it for it in items if f.keep(ctx, it)]

        # 4. Scorers sequential
        scored: list[ScoredItem[Item]] = [ScoredItem(item=it) for it in items]
        for s in self.scorers:
            await s.score(ctx, scored)

        # 5. Selector
        selected = self.selector.select(ctx, scored, k)

        # 6. Side effects fire-and-forget
        for se in self.side_effects:
            asyncio.create_task(self._safe_emit(se, ctx, selected))

        return selected

    async def _safe_fetch(self, s: Source[Ctx, Item], ctx: Ctx) -> list[Item]:
        try:
            return await s.fetch(ctx)
        except Exception as e:
            log.warning("Source %s failed: %s", s.name, e)
            return []

    async def _safe_hydrate(self, h: Hydrator[Ctx, Item], ctx: Ctx, items: list[Item]) -> None:
        try:
            await h.hydrate(ctx, items)
        except Exception as e:
            log.warning("Hydrator %s failed: %s", h.name, e)

    async def _safe_emit(self, se: SideEffect[Ctx, Item], ctx: Ctx, items: list[ScoredItem[Item]]) -> None:
        try:
            await se.emit(ctx, items)
        except Exception as e:
            log.warning("SideEffect %s failed: %s", se.name, e)
