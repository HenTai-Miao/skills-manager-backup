package pipeline

import (
	"context"
	"errors"
	"testing"
	"time"
)

type testCtx struct{ UserID int }
type testItem struct {
	ID       int
	AuthorID int
	Title    string
}

type fakeSource struct {
	name  string
	delay time.Duration
	items []testItem
	err   error
}

func (s *fakeSource) Name() string { return s.name }
func (s *fakeSource) Fetch(ctx context.Context, c testCtx) ([]testItem, error) {
	if s.delay > 0 {
		time.Sleep(s.delay)
	}
	return s.items, s.err
}

type evenFilter struct{}

func (evenFilter) Name() string                                          { return "even" }
func (evenFilter) Keep(_ context.Context, _ testCtx, item testItem) bool { return item.ID%2 == 0 }

type idScorer struct{}

func (idScorer) Name() string { return "id" }
func (idScorer) Score(_ context.Context, _ testCtx, items []ScoredItem[testItem]) error {
	for i := range items {
		items[i].Score = float64(items[i].Item.ID)
	}
	return nil
}

type topKSelector struct{}

func (topKSelector) Name() string { return "topk" }
func (topKSelector) Select(_ testCtx, items []ScoredItem[testItem], k int) []ScoredItem[testItem] {
	SortByScoreDesc(items)
	if k > len(items) {
		k = len(items)
	}
	return items[:k]
}

func TestPipelineFiltersAndSorts(t *testing.T) {
	p := &Pipeline[testCtx, testItem]{
		Sources: []Source[testCtx, testItem]{
			&fakeSource{
				name: "s1",
				items: []testItem{
					{ID: 1, AuthorID: 10, Title: "a"},
					{ID: 2, AuthorID: 10, Title: "b"},
					{ID: 3, AuthorID: 20, Title: "c"},
					{ID: 4, AuthorID: 20, Title: "d"},
				},
			},
		},
		Filters:  []Filter[testCtx, testItem]{evenFilter{}},
		Scorers:  []Scorer[testCtx, testItem]{idScorer{}},
		Selector: topKSelector{},
	}

	result, err := p.Run(context.Background(), testCtx{UserID: 1}, 5)
	if err != nil {
		t.Fatalf("Run failed: %v", err)
	}

	if len(result) != 2 {
		t.Fatalf("expected 2 results (even IDs), got %d", len(result))
	}
	if result[0].Item.ID != 4 || result[1].Item.ID != 2 {
		t.Errorf("expected [4, 2], got [%d, %d]", result[0].Item.ID, result[1].Item.ID)
	}
}

func TestPipelineSourcesParallel(t *testing.T) {
	p := &Pipeline[testCtx, testItem]{
		Sources: []Source[testCtx, testItem]{
			&fakeSource{name: "s1", delay: 50 * time.Millisecond, items: []testItem{{ID: 1}}},
			&fakeSource{name: "s2", delay: 50 * time.Millisecond, items: []testItem{{ID: 2}}},
			&fakeSource{name: "s3", delay: 50 * time.Millisecond, items: []testItem{{ID: 3}}},
		},
		Selector: topKSelector{},
	}

	start := time.Now()
	_, err := p.Run(context.Background(), testCtx{UserID: 1}, 10)
	elapsed := time.Since(start)

	if err != nil {
		t.Fatal(err)
	}
	// Sequential: ~150ms. Parallel: ~50ms. Generous bound.
	if elapsed > 120*time.Millisecond {
		t.Errorf("sources appear sequential: took %v", elapsed)
	}
}

func TestPipelineSurvivesSourceError(t *testing.T) {
	p := &Pipeline[testCtx, testItem]{
		Sources: []Source[testCtx, testItem]{
			&fakeSource{name: "good", items: []testItem{{ID: 1}}},
			&fakeSource{name: "bad", err: errors.New("boom")},
		},
		Selector: topKSelector{},
	}

	result, err := p.Run(context.Background(), testCtx{UserID: 1}, 10)
	if err != nil {
		t.Fatal(err)
	}
	if len(result) != 1 || result[0].Item.ID != 1 {
		t.Errorf("expected single item ID=1, got %v", result)
	}
}
