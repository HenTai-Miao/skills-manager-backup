package pipeline

import (
	"context"
	"log"
	"sort"
	"sync"
)

// Pipeline composes the six stages and runs them in order.
type Pipeline[Ctx any, Item any] struct {
	Sources     []Source[Ctx, Item]
	Hydrators   []Hydrator[Ctx, Item]
	Filters     []Filter[Ctx, Item]
	Scorers     []Scorer[Ctx, Item]
	Selector    Selector[Ctx, Item]
	SideEffects []SideEffect[Ctx, Item]

	// Logger receives stage-level events. If nil, log.Default() is used.
	Logger *log.Logger
}

// Run executes the pipeline end-to-end and returns the top K scored items.
func (p *Pipeline[Ctx, Item]) Run(ctx context.Context, c Ctx, k int) ([]ScoredItem[Item], error) {
	logger := p.Logger
	if logger == nil {
		logger = log.Default()
	}

	// 1. Sources in parallel
	items := p.runSources(ctx, c, logger)

	// 2. Hydrators in parallel
	p.runHydrators(ctx, c, items, logger)

	// 3. Filters sequentially
	items = p.runFilters(ctx, c, items, logger)

	// 4. Scorers sequentially
	scored := make([]ScoredItem[Item], len(items))
	for i, it := range items {
		scored[i] = ScoredItem[Item]{
			Item:       it,
			Score:      0,
			Components: make(map[string]float64),
		}
	}
	for _, s := range p.Scorers {
		if err := s.Score(ctx, c, scored); err != nil {
			logger.Printf("scorer %s failed: %v", s.Name(), err)
		}
	}

	// 5. Selector
	selected := p.Selector.Select(c, scored, k)

	// 6. SideEffects fire-and-forget
	for _, se := range p.SideEffects {
		go func(se SideEffect[Ctx, Item]) {
			defer func() {
				if r := recover(); r != nil {
					logger.Printf("side effect %s panicked: %v", se.Name(), r)
				}
			}()
			se.Emit(c, selected)
		}(se)
	}

	return selected, nil
}

func (p *Pipeline[Ctx, Item]) runSources(ctx context.Context, c Ctx, logger *log.Logger) []Item {
	var (
		mu     sync.Mutex
		all    []Item
		wg     sync.WaitGroup
	)
	for _, s := range p.Sources {
		wg.Add(1)
		go func(s Source[Ctx, Item]) {
			defer wg.Done()
			items, err := s.Fetch(ctx, c)
			if err != nil {
				logger.Printf("source %s failed: %v", s.Name(), err)
				return
			}
			mu.Lock()
			all = append(all, items...)
			mu.Unlock()
		}(s)
	}
	wg.Wait()
	return all
}

func (p *Pipeline[Ctx, Item]) runHydrators(ctx context.Context, c Ctx, items []Item, logger *log.Logger) {
	var wg sync.WaitGroup
	for _, h := range p.Hydrators {
		wg.Add(1)
		go func(h Hydrator[Ctx, Item]) {
			defer wg.Done()
			if err := h.Hydrate(ctx, c, items); err != nil {
				logger.Printf("hydrator %s failed: %v", h.Name(), err)
			}
		}(h)
	}
	wg.Wait()
}

func (p *Pipeline[Ctx, Item]) runFilters(ctx context.Context, c Ctx, items []Item, logger *log.Logger) []Item {
	for _, f := range p.Filters {
		kept := make([]Item, 0, len(items))
		for _, it := range items {
			if f.Keep(ctx, c, it) {
				kept = append(kept, it)
			}
		}
		items = kept
	}
	return items
}

// SortByScoreDesc is a helper for Selector implementations.
func SortByScoreDesc[Item any](items []ScoredItem[Item]) {
	sort.Slice(items, func(i, j int) bool {
		return items[i].Score > items[j].Score
	})
}
