import {
  Source, Hydrator, Filter, Scorer, Selector, SideEffect, ScoredItem,
} from './interfaces';

export interface PipelineConfig<Ctx, Item> {
  sources: Source<Ctx, Item>[];
  hydrators: Hydrator<Ctx, Item>[];
  filters: Filter<Ctx, Item>[];
  scorers: Scorer<Ctx, Item>[];
  selector: Selector<Ctx, Item>;
  sideEffects: SideEffect<Ctx, Item>[];
}

export class Pipeline<Ctx, Item> {
  constructor(private config: PipelineConfig<Ctx, Item>) {}

  async run(ctx: Ctx, k: number): Promise<ScoredItem<Item>[]> {
    // 1. Sources in parallel
    const sourceResults = await Promise.all(
      this.config.sources.map(s => s.fetch(ctx).catch(err => {
        console.error(`Source ${s.name} failed:`, err);
        return [] as Item[];
      }))
    );
    let items: Item[] = sourceResults.flat();

    // 2. Hydrators in parallel (each enriches the full set)
    await Promise.all(
      this.config.hydrators.map(h =>
        h.hydrate(ctx, items).catch(err => {
          console.error(`Hydrator ${h.name} failed:`, err);
        })
      )
    );

    // 3. Filters sequentially
    for (const f of this.config.filters) {
      const checks = await Promise.all(
        items.map(item => Promise.resolve(f.keep(ctx, item)))
      );
      items = items.filter((_, i) => checks[i]);
    }

    // 4. Scorers sequentially (each sees previous scores)
    let scored: ScoredItem<Item>[] = items.map(item => ({
      item,
      score: 0,
      components: {},
    }));
    for (const s of this.config.scorers) {
      await s.score(ctx, scored);
    }

    // 5. Selector
    const selected = this.config.selector.select(ctx, scored, k);

    // 6. SideEffects fire-and-forget
    for (const se of this.config.sideEffects) {
      Promise.resolve(se.emit(ctx, selected)).catch(err => {
        console.error(`SideEffect ${se.name} failed:`, err);
      });
    }

    return selected;
  }
}
