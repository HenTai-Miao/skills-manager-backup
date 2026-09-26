// Pipeline interfaces — composable recommendation framework
// Pattern inspired by xAI's open-sourced X For You algorithm (Apache 2.0)
// Reimplemented from scratch in TypeScript

export interface ScoredItem<Item> {
  item: Item;
  score: number;
  components?: Record<string, number>;
}

export interface Source<Ctx, Item> {
  name: string;
  fetch(ctx: Ctx): Promise<Item[]>;
}

export interface Hydrator<Ctx, Item> {
  name: string;
  hydrate(ctx: Ctx, items: Item[]): Promise<void>;
}

export interface Filter<Ctx, Item> {
  name: string;
  keep(ctx: Ctx, item: Item): boolean | Promise<boolean>;
}

export interface Scorer<Ctx, Item> {
  name: string;
  score(ctx: Ctx, items: ScoredItem<Item>[]): Promise<void>;
}

export interface Selector<Ctx, Item> {
  name: string;
  select(ctx: Ctx, items: ScoredItem<Item>[], k: number): ScoredItem<Item>[];
}

export interface SideEffect<Ctx, Item> {
  name: string;
  emit(ctx: Ctx, items: ScoredItem<Item>[]): void | Promise<void>;
}
