// Package recsys exposes the pipeline framework as a Zentra engine.Module.
//
// Standalone usage (without Zentra) is in pipeline/.
package recsys

import (
	"context"

	"github.com/turac/zentra-recsys-pipeline/pipeline"
)

// Module is a Zentra-compatible adapter around a configured pipeline.
//
// Implements (informally) the engine.Module interface:
//   - Name() string
//   - Init(config map[string]any) error
//   - Handle(ctx context.Context, req any) (any, error)
//   - Shutdown() error
//
// Replace the concrete Ctx and Item types with your domain.
type Module[Ctx any, Item any] struct {
	pipe *pipeline.Pipeline[Ctx, Item]
}

func NewModule[Ctx any, Item any](pipe *pipeline.Pipeline[Ctx, Item]) *Module[Ctx, Item] {
	return &Module[Ctx, Item]{pipe: pipe}
}

func (m *Module[Ctx, Item]) Name() string { return "recsys-pipeline" }

func (m *Module[Ctx, Item]) Init(config map[string]any) error {
	// Wire config-driven knobs here (weights, decay rates, etc.)
	return nil
}

// Request is the Module's input. Adapt to Zentra's request envelope.
type Request[Ctx any] struct {
	Ctx Ctx
	K   int
}

// Response is the Module's output.
type Response[Item any] struct {
	Items []pipeline.ScoredItem[Item]
}

func (m *Module[Ctx, Item]) Handle(ctx context.Context, req *Request[Ctx]) (*Response[Item], error) {
	results, err := m.pipe.Run(ctx, req.Ctx, req.K)
	if err != nil {
		return nil, err
	}
	return &Response[Item]{Items: results}, nil
}

func (m *Module[Ctx, Item]) Shutdown() error { return nil }
