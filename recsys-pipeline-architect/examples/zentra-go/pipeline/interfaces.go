// Package pipeline implements the six-stage composable recommendation framework.
//
// Stages:
//   1. Source     — fetch candidates
//   2. Hydrator   — enrich with metadata
//   3. Filter     — drop ineligible
//   4. Scorer     — assign scores
//   5. Selector   — sort and pick top K
//   6. SideEffect — fire async post-actions
//
// Pattern inspired by xAI's open-sourced X For You algorithm (Apache 2.0).
// This is an independent reimplementation in Go.
package pipeline

import "context"

// ScoredItem wraps an Item with its assigned score and per-component breakdown.
type ScoredItem[Item any] struct {
	Item       Item
	Score      float64
	Components map[string]float64
}

// Source fetches candidate items from one origin.
// Sources run in parallel.
type Source[Ctx any, Item any] interface {
	Name() string
	Fetch(ctx context.Context, c Ctx) ([]Item, error)
}

// Hydrator enriches items with metadata.
// Hydrators run in parallel, each over the full candidate set.
type Hydrator[Ctx any, Item any] interface {
	Name() string
	Hydrate(ctx context.Context, c Ctx, items []Item) error
}

// Filter drops items that should not be shown.
// Filters run sequentially; cheaper checks first.
type Filter[Ctx any, Item any] interface {
	Name() string
	Keep(ctx context.Context, c Ctx, item Item) bool
}

// Scorer assigns scores to items.
// Scorers run sequentially; later scorers see earlier scores.
type Scorer[Ctx any, Item any] interface {
	Name() string
	Score(ctx context.Context, c Ctx, items []ScoredItem[Item]) error
}

// Selector picks the top K from scored items.
type Selector[Ctx any, Item any] interface {
	Name() string
	Select(c Ctx, items []ScoredItem[Item], k int) []ScoredItem[Item]
}

// SideEffect fires async actions after selection.
// Errors are logged but never returned to the caller.
type SideEffect[Ctx any, Item any] interface {
	Name() string
	Emit(c Ctx, items []ScoredItem[Item])
}
