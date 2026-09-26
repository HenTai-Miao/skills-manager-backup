"""End-to-end test of the task pipeline. Verifies stage order and filter behavior."""
import asyncio
import time
import sys
from pathlib import Path

# Allow `from pipeline import ...` from this test file
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from pipeline import Pipeline, ScoredItem


# Shared fixtures
class Ctx:
    def __init__(self, user_id=1):
        self.user_id = user_id


class Item:
    def __init__(self, id, author_id):
        self.id = id
        self.author_id = author_id


class TraceSource:
    def __init__(self, items, name="src", trace=None, delay=0):
        self.items = items
        self.name = name
        self.trace = trace if trace is not None else []
        self.delay = delay

    async def fetch(self, _ctx):
        if self.delay:
            await asyncio.sleep(self.delay)
        self.trace.append(f"source:{self.name}")
        return list(self.items)


class FailingSource:
    name = "bad"
    async def fetch(self, _ctx):
        raise RuntimeError("source down")


class TraceHydrator:
    name = "hyd"
    def __init__(self, trace):
        self.trace = trace
    async def hydrate(self, _ctx, _items):
        self.trace.append("hydrator")


class KeepEvenFilter:
    name = "even"
    def __init__(self, trace):
        self.trace = trace
    def keep(self, _ctx, item):
        self.trace.append(f"filter:{item.id}")
        return item.id % 2 == 0


class IdScorer:
    name = "id_score"
    def __init__(self, trace):
        self.trace = trace
    async def score(self, _ctx, items):
        self.trace.append("scorer")
        for s in items:
            s.score = float(s.item.id)


class TopK:
    name = "topk"
    def __init__(self, trace):
        self.trace = trace
    def select(self, _ctx, items, k):
        self.trace.append("selector")
        return sorted(items, key=lambda s: s.score, reverse=True)[:k]


class TraceSideEffect:
    name = "se"
    def __init__(self, trace):
        self.trace = trace
    async def emit(self, _ctx, _items):
        self.trace.append("side_effect")


@pytest.mark.asyncio
async def test_stages_run_in_order():
    trace = []
    items = [Item(1, 10), Item(2, 10), Item(3, 20)]
    pipe = Pipeline(
        sources=[TraceSource(items, trace=trace)],
        hydrators=[TraceHydrator(trace)],
        filters=[KeepEvenFilter(trace)],
        scorers=[IdScorer(trace)],
        selector=TopK(trace),
        side_effects=[TraceSideEffect(trace)],
    )

    result = await pipe.run(Ctx(), 10)

    assert [r.item.id for r in result] == [2]

    # Wait briefly for the fire-and-forget side effect
    await asyncio.sleep(0.05)

    stage_order = [t for t in trace if ":" not in t]
    assert stage_order == ["hydrator", "scorer", "selector", "side_effect"]
    assert trace[0] == "source:src"


@pytest.mark.asyncio
async def test_sources_run_in_parallel():
    trace = []
    items_a = [Item(1, 10)]
    items_b = [Item(2, 10)]
    items_c = [Item(3, 10)]

    pipe = Pipeline(
        sources=[
            TraceSource(items_a, name="a", trace=trace, delay=0.05),
            TraceSource(items_b, name="b", trace=trace, delay=0.05),
            TraceSource(items_c, name="c", trace=trace, delay=0.05),
        ],
        hydrators=[],
        filters=[],
        scorers=[],
        selector=TopK(trace),
        side_effects=[],
    )

    start = time.perf_counter()
    await pipe.run(Ctx(), 10)
    elapsed = time.perf_counter() - start

    # Sequential would be ~150ms; parallel ~50ms. Generous bound.
    assert elapsed < 0.12, f"sources appear sequential: took {elapsed:.3f}s"


@pytest.mark.asyncio
async def test_survives_source_error():
    trace = []
    good_items = [Item(1, 10)]
    pipe = Pipeline(
        sources=[
            TraceSource(good_items, name="good", trace=trace),
            FailingSource(),
        ],
        hydrators=[],
        filters=[],
        scorers=[],
        selector=TopK(trace),
        side_effects=[],
    )
    result = await pipe.run(Ctx(), 10)
    assert len(result) == 1
    assert result[0].item.id == 1
