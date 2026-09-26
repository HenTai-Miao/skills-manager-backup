import { Pipeline } from '../src/pipeline/runner';
import { Source, Hydrator, Filter, Scorer, Selector, SideEffect, ScoredItem } from '../src/pipeline/interfaces';

interface TestCtx { userId: number; }
interface TestItem { id: number; authorId: number; title: string; }

describe('Pipeline', () => {
  it('runs the six stages in order', async () => {
    const callOrder: string[] = [];

    const source: Source<TestCtx, TestItem> = {
      name: 'src',
      async fetch() {
        callOrder.push('source');
        return [
          { id: 1, authorId: 10, title: 'a' },
          { id: 2, authorId: 10, title: 'b' },
          { id: 3, authorId: 20, title: 'c' },
        ];
      },
    };

    const hydrator: Hydrator<TestCtx, TestItem> = {
      name: 'hyd',
      async hydrate() { callOrder.push('hydrator'); },
    };

    const filter: Filter<TestCtx, TestItem> = {
      name: 'fil',
      keep(_ctx, item) {
        callOrder.push(`filter:${item.id}`);
        return item.id !== 2;
      },
    };

    const scorer: Scorer<TestCtx, TestItem> = {
      name: 'sc',
      async score(_ctx, items) {
        callOrder.push('scorer');
        for (const s of items) s.score = s.item.id;
      },
    };

    const selector: Selector<TestCtx, TestItem> = {
      name: 'sel',
      select(_ctx, items, k) {
        callOrder.push('selector');
        return [...items].sort((a, b) => b.score - a.score).slice(0, k);
      },
    };

    const sideEffect: SideEffect<TestCtx, TestItem> = {
      name: 'se',
      emit() { callOrder.push('side_effect'); },
    };

    const pipeline = new Pipeline<TestCtx, TestItem>({
      sources: [source],
      hydrators: [hydrator],
      filters: [filter],
      scorers: [scorer],
      selector,
      sideEffects: [sideEffect],
    });

    const result = await pipeline.run({ userId: 1 }, 10);

    // Filter dropped id=2
    expect(result.map(r => r.item.id)).toEqual([3, 1]);

    // Stage order
    const stageOrder = callOrder.filter(s => !s.startsWith('filter:'));
    expect(stageOrder).toEqual(['source', 'hydrator', 'scorer', 'selector', 'side_effect']);
  });

  it('runs sources in parallel', async () => {
    const sourceTimings: { name: string; t: number }[] = [];

    const makeSource = (name: string, delay: number): Source<TestCtx, TestItem> => ({
      name,
      async fetch() {
        const start = Date.now();
        await new Promise(r => setTimeout(r, delay));
        sourceTimings.push({ name, t: Date.now() - start });
        return [{ id: 1, authorId: 10, title: name }];
      },
    });

    const pipeline = new Pipeline<TestCtx, TestItem>({
      sources: [
        makeSource('s1', 50),
        makeSource('s2', 50),
        makeSource('s3', 50),
      ],
      hydrators: [],
      filters: [],
      scorers: [],
      selector: {
        name: 'sel',
        select: (_ctx, items, k) => items.slice(0, k),
      },
      sideEffects: [],
    });

    const start = Date.now();
    await pipeline.run({ userId: 1 }, 10);
    const total = Date.now() - start;

    // Sequential would take ~150ms; parallel ~50ms. Allow generous margin.
    expect(total).toBeLessThan(120);
  });

  it('survives a source error', async () => {
    const goodSource: Source<TestCtx, TestItem> = {
      name: 'good',
      async fetch() { return [{ id: 1, authorId: 10, title: 'a' }]; },
    };

    const badSource: Source<TestCtx, TestItem> = {
      name: 'bad',
      async fetch() { throw new Error('source down'); },
    };

    const pipeline = new Pipeline<TestCtx, TestItem>({
      sources: [goodSource, badSource],
      hydrators: [],
      filters: [],
      scorers: [],
      selector: {
        name: 'sel',
        select: (_ctx, items, k) => items.slice(0, k),
      },
      sideEffects: [],
    });

    const result = await pipeline.run({ userId: 1 }, 10);
    expect(result.length).toBe(1);
    expect(result[0].item.id).toBe(1);
  });
});
