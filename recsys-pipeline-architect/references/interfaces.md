# Pipeline Interface Definitions

Six-stage pipeline interfaces in four languages. Generated scaffolds derive from these.

The interfaces are intentionally minimal. Add `context.Context`, error types, telemetry hooks per your stack — but keep the core six interfaces clean.

---

## TypeScript / Node

```typescript
// Item is whatever you're ranking (Post, Article, Task, etc.)
// Context is whatever drives the ranking (UserId, Query, etc.)

export interface Source<Ctx, Item> {
  name: string;
  fetch(ctx: Ctx): Promise<Item[]>;
}

export interface Hydrator<Ctx, Item> {
  name: string;
  hydrate(ctx: Ctx, items: Item[]): Promise<Item[]>;
}

export interface Filter<Ctx, Item> {
  name: string;
  // Return true to keep the item, false to drop
  predicate(ctx: Ctx, item: Item): boolean | Promise<boolean>;
}

export interface Scorer<Ctx, Item> {
  name: string;
  // Mutates item.score, or returns a new array with scores attached
  score(ctx: Ctx, items: ScoredItem<Item>[]): Promise<ScoredItem<Item>[]>;
}

export interface Selector<Ctx, Item> {
  name: string;
  select(ctx: Ctx, items: ScoredItem<Item>[], k: number): ScoredItem<Item>[];
}

export interface SideEffect<Ctx, Item> {
  name: string;
  // Fired async, must not throw
  emit(ctx: Ctx, items: ScoredItem<Item>[]): void;
}

export interface ScoredItem<Item> {
  item: Item;
  score: number;
  components?: Record<string, number>; // optional per-scorer breakdown
}

// The pipeline runner
export class Pipeline<Ctx, Item> {
  constructor(
    private sources: Source<Ctx, Item>[],
    private hydrators: Hydrator<Ctx, Item>[],
    private filters: Filter<Ctx, Item>[],
    private scorers: Scorer<Ctx, Item>[],
    private selector: Selector<Ctx, Item>,
    private sideEffects: SideEffect<Ctx, Item>[],
  ) {}

  async run(ctx: Ctx, k: number): Promise<ScoredItem<Item>[]> {
    // 1. Sources in parallel
    const candidateArrays = await Promise.all(
      this.sources.map(s => s.fetch(ctx))
    );
    let items = candidateArrays.flat();

    // 2. Hydrators in parallel (each enriches the full set)
    await Promise.all(this.hydrators.map(h => h.hydrate(ctx, items)));

    // 3. Filters sequentially
    for (const f of this.filters) {
      const keepers: Item[] = [];
      for (const item of items) {
        if (await f.predicate(ctx, item)) keepers.push(item);
      }
      items = keepers;
    }

    // 4. Scorers sequentially (each sees previous scores)
    let scored: ScoredItem<Item>[] = items.map(item => ({ item, score: 0 }));
    for (const s of this.scorers) {
      scored = await s.score(ctx, scored);
    }

    // 5. Selector
    const selected = this.selector.select(ctx, scored, k);

    // 6. Side effects fire-and-forget
    for (const se of this.sideEffects) {
      try { se.emit(ctx, selected); } catch (e) { /* log, never throw */ }
    }

    return selected;
  }
}
```

---

## Go

```go
package pipeline

import "context"

type Source[Ctx any, Item any] interface {
    Name() string
    Fetch(ctx context.Context, c Ctx) ([]Item, error)
}

type Hydrator[Ctx any, Item any] interface {
    Name() string
    Hydrate(ctx context.Context, c Ctx, items []Item) error
}

type Filter[Ctx any, Item any] interface {
    Name() string
    Keep(ctx context.Context, c Ctx, item Item) bool
}

type ScoredItem[Item any] struct {
    Item       Item
    Score      float64
    Components map[string]float64
}

type Scorer[Ctx any, Item any] interface {
    Name() string
    Score(ctx context.Context, c Ctx, items []ScoredItem[Item]) error
}

type Selector[Ctx any, Item any] interface {
    Name() string
    Select(c Ctx, items []ScoredItem[Item], k int) []ScoredItem[Item]
}

type SideEffect[Ctx any, Item any] interface {
    Name() string
    Emit(c Ctx, items []ScoredItem[Item])
}

type Pipeline[Ctx any, Item any] struct {
    Sources     []Source[Ctx, Item]
    Hydrators   []Hydrator[Ctx, Item]
    Filters     []Filter[Ctx, Item]
    Scorers     []Scorer[Ctx, Item]
    Selector    Selector[Ctx, Item]
    SideEffects []SideEffect[Ctx, Item]
}

func (p *Pipeline[Ctx, Item]) Run(ctx context.Context, c Ctx, k int) ([]ScoredItem[Item], error) {
    // 1. Sources in parallel via errgroup (left to the implementer)
    // 2. Hydrators in parallel
    // 3. Filters sequential
    // 4. Scorers sequential
    // 5. Selector
    // 6. SideEffects in goroutines
    //
    // Full implementation in examples/zentra-go/pipeline.go
}
```

---

## Python (async)

```python
from typing import Generic, TypeVar, Protocol, runtime_checkable
from dataclasses import dataclass, field
import asyncio

Ctx = TypeVar('Ctx')
Item = TypeVar('Item')

@dataclass
class ScoredItem(Generic[Item]):
    item: Item
    score: float = 0.0
    components: dict[str, float] = field(default_factory=dict)


@runtime_checkable
class Source(Protocol, Generic[Ctx, Item]):
    name: str
    async def fetch(self, ctx: Ctx) -> list[Item]: ...


@runtime_checkable
class Hydrator(Protocol, Generic[Ctx, Item]):
    name: str
    async def hydrate(self, ctx: Ctx, items: list[Item]) -> None: ...


@runtime_checkable
class Filter(Protocol, Generic[Ctx, Item]):
    name: str
    async def keep(self, ctx: Ctx, item: Item) -> bool: ...


@runtime_checkable
class Scorer(Protocol, Generic[Ctx, Item]):
    name: str
    async def score(self, ctx: Ctx, items: list[ScoredItem[Item]]) -> None: ...


@runtime_checkable
class Selector(Protocol, Generic[Ctx, Item]):
    name: str
    def select(self, ctx: Ctx, items: list[ScoredItem[Item]], k: int) -> list[ScoredItem[Item]]: ...


@runtime_checkable
class SideEffect(Protocol, Generic[Ctx, Item]):
    name: str
    async def emit(self, ctx: Ctx, items: list[ScoredItem[Item]]) -> None: ...


class Pipeline(Generic[Ctx, Item]):
    def __init__(self, sources, hydrators, filters_, scorers, selector, side_effects):
        self.sources = sources
        self.hydrators = hydrators
        self.filters = filters_
        self.scorers = scorers
        self.selector = selector
        self.side_effects = side_effects

    async def run(self, ctx: Ctx, k: int) -> list[ScoredItem[Item]]:
        # 1. Sources parallel
        results = await asyncio.gather(*[s.fetch(ctx) for s in self.sources])
        items = [item for batch in results for item in batch]

        # 2. Hydrators parallel
        await asyncio.gather(*[h.hydrate(ctx, items) for h in self.hydrators])

        # 3. Filters sequential
        for f in self.filters:
            checks = await asyncio.gather(*[f.keep(ctx, item) for item in items])
            items = [item for item, keep in zip(items, checks) if keep]

        # 4. Scorers sequential
        scored = [ScoredItem(item=item) for item in items]
        for s in self.scorers:
            await s.score(ctx, scored)

        # 5. Selector
        selected = self.selector.select(ctx, scored, k)

        # 6. SideEffects fire-and-forget
        for se in self.side_effects:
            asyncio.create_task(se.emit(ctx, selected))

        return selected
```

---

## Rust (sketch)

```rust
use async_trait::async_trait;

#[async_trait]
pub trait Source<Ctx, Item>: Send + Sync {
    fn name(&self) -> &str;
    async fn fetch(&self, ctx: &Ctx) -> Result<Vec<Item>, anyhow::Error>;
}

#[async_trait]
pub trait Hydrator<Ctx, Item>: Send + Sync {
    fn name(&self) -> &str;
    async fn hydrate(&self, ctx: &Ctx, items: &mut [Item]) -> Result<(), anyhow::Error>;
}

#[async_trait]
pub trait Filter<Ctx, Item>: Send + Sync {
    fn name(&self) -> &str;
    async fn keep(&self, ctx: &Ctx, item: &Item) -> bool;
}

pub struct ScoredItem<Item> {
    pub item: Item,
    pub score: f64,
    pub components: std::collections::HashMap<String, f64>,
}

#[async_trait]
pub trait Scorer<Ctx, Item>: Send + Sync {
    fn name(&self) -> &str;
    async fn score(&self, ctx: &Ctx, items: &mut [ScoredItem<Item>]) -> Result<(), anyhow::Error>;
}

pub trait Selector<Ctx, Item>: Send + Sync {
    fn name(&self) -> &str;
    fn select(&self, ctx: &Ctx, items: Vec<ScoredItem<Item>>, k: usize) -> Vec<ScoredItem<Item>>;
}

#[async_trait]
pub trait SideEffect<Ctx, Item>: Send + Sync {
    fn name(&self) -> &str;
    async fn emit(&self, ctx: &Ctx, items: &[ScoredItem<Item>]);
}
```

The Rust version most closely mirrors the original X For You implementation in the `candidate-pipeline` crate.

---

## Notes on the interfaces

- All hydrators mutate in place. They enrich items; they do not return new arrays.
- All filters use a "keep" predicate (returns true to keep). This reads better than "drop" predicates: `if (await filter.keep(item))`.
- Scorers operate on `ScoredItem<Item>`, not `Item`. This lets later scorers see earlier scores and add their own component.
- The `components` map on `ScoredItem` is for debugging and tuning. In production, log it.
- The Pipeline class is generic over both `Ctx` (driver of ranking, e.g., user ID) and `Item` (thing being ranked). Do not collapse these into one type.
