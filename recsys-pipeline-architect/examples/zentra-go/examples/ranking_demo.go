// Standalone demo: a toy pipeline that ranks articles by recency + topic match.
// Run: go run examples/ranking_demo.go
package main

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/turac/zentra-recsys-pipeline/pipeline"
)

type Ctx struct {
	UserID            int
	PreferredTopics   []string
	FollowedAuthorIDs []int
}

type Article struct {
	ID        int
	AuthorID  int
	Title     string
	Topic     string
	Published time.Time
}

// ---- Source ----
type recentSource struct{ all []Article }

func (s *recentSource) Name() string { return "recent" }
func (s *recentSource) Fetch(_ context.Context, c Ctx) ([]Article, error) {
	out := make([]Article, len(s.all))
	copy(out, s.all)
	return out, nil
}

// ---- Filter ----
type ageFilter struct{ maxAge time.Duration }

func (f ageFilter) Name() string { return "age" }
func (f ageFilter) Keep(_ context.Context, _ Ctx, a Article) bool {
	return time.Since(a.Published) < f.maxAge
}

// ---- Scorers ----
type topicMatchScorer struct{}

func (topicMatchScorer) Name() string { return "topic_match" }
func (topicMatchScorer) Score(_ context.Context, c Ctx, items []pipeline.ScoredItem[Article]) error {
	for i := range items {
		for _, pref := range c.PreferredTopics {
			if strings.EqualFold(pref, items[i].Item.Topic) {
				items[i].Score += 1.0
				items[i].Components["topic_match"] = 1.0
				break
			}
		}
	}
	return nil
}

type followedAuthorScorer struct{}

func (followedAuthorScorer) Name() string { return "followed_author" }
func (followedAuthorScorer) Score(_ context.Context, c Ctx, items []pipeline.ScoredItem[Article]) error {
	for i := range items {
		for _, fid := range c.FollowedAuthorIDs {
			if items[i].Item.AuthorID == fid {
				items[i].Score += 2.0
				items[i].Components["followed_author"] = 2.0
				break
			}
		}
	}
	return nil
}

// ---- Selector ----
type topK struct{}

func (topK) Name() string { return "topk" }
func (topK) Select(_ Ctx, items []pipeline.ScoredItem[Article], k int) []pipeline.ScoredItem[Article] {
	pipeline.SortByScoreDesc(items)
	if k > len(items) {
		k = len(items)
	}
	return items[:k]
}

func main() {
	now := time.Now()
	articles := []Article{
		{ID: 1, AuthorID: 10, Title: "Rust eats the world", Topic: "rust", Published: now.Add(-1 * time.Hour)},
		{ID: 2, AuthorID: 11, Title: "Go is fine actually", Topic: "go", Published: now.Add(-3 * time.Hour)},
		{ID: 3, AuthorID: 10, Title: "Tokio internals", Topic: "rust", Published: now.Add(-10 * time.Hour)},
		{ID: 4, AuthorID: 12, Title: "Pandas tricks", Topic: "python", Published: now.Add(-2 * time.Hour)},
		{ID: 5, AuthorID: 13, Title: "Old news", Topic: "rust", Published: now.Add(-100 * time.Hour)},
	}

	p := &pipeline.Pipeline[Ctx, Article]{
		Sources:  []pipeline.Source[Ctx, Article]{&recentSource{all: articles}},
		Filters:  []pipeline.Filter[Ctx, Article]{ageFilter{maxAge: 48 * time.Hour}},
		Scorers:  []pipeline.Scorer[Ctx, Article]{topicMatchScorer{}, followedAuthorScorer{}},
		Selector: topK{},
	}

	ctx := Ctx{
		UserID:            1,
		PreferredTopics:   []string{"rust"},
		FollowedAuthorIDs: []int{10},
	}

	results, err := p.Run(context.Background(), ctx, 3)
	if err != nil {
		panic(err)
	}

	fmt.Println("Top 3 for user 1:")
	for i, r := range results {
		fmt.Printf("  %d. [score %.2f] %s (by %d, components: %v)\n",
			i+1, r.Score, r.Item.Title, r.Item.AuthorID, r.Components)
	}
}
