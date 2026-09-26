# Zentra Pipeline Example (Go)

A Go implementation of the composable recommendation pipeline, packaged as a Zentra-compatible plugin module (`engine.Module` interface).

Zentra is a cognitive data plane gateway. Its plugin architecture exposes an `engine.Module` interface that any module must implement. This example wraps the six-stage pipeline framework as a Zentra module so that recommendation/ranking logic plugs in alongside other modules (auth, cache, LLM gateway, etc.).

If you don't use Zentra, the `pipeline/` package is standalone Go — strip the `module.go` file and use it directly.

## Files

```
zentra-go/
├── README.md
├── go.mod
├── pipeline/
│   ├── interfaces.go          # Source/Hydrator/Filter/Scorer/Selector/SideEffect
│   ├── pipeline.go            # the Pipeline struct + Run method
│   └── pipeline_test.go
├── module.go                  # Zentra engine.Module adapter
└── examples/
    └── ranking_demo.go        # standalone main, runs a toy pipeline
```

## Standalone usage

```bash
cd zentra-go
go test ./pipeline/
go run examples/ranking_demo.go
```

## Zentra module usage

Register the module with Zentra's engine:

```go
import "your/path/zentra-go"

func init() {
    engine.Register("recsys-pipeline", recsys.NewModule())
}
```

The module exposes a configurable pipeline whose stages are wired through Zentra's config file.

## Attribution

The six-stage pipeline pattern is inspired by xAI's open-sourced X For You algorithm (Apache 2.0). This implementation is independent and licensed under MIT.

Reference: https://github.com/xai-org/x-algorithm
