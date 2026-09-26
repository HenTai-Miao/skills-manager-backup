import { Scorer, ScoredItem } from '../interfaces';
import { FeedContext, Article } from '../types';

export interface FeedWeights {
  read: number;
  like: number;
  share: number;
  skip: number; // typically negative
  // extendable: block_author, mute_author, report — all negative
}

export const DEFAULT_WEIGHTS: FeedWeights = {
  read: 1.0,
  like: 2.0,
  share: 3.0,
  skip: -1.0,
};

export class WeightedSumCombiner implements Scorer<FeedContext, Article> {
  name = 'weighted_sum';
  constructor(private readonly weights: FeedWeights = DEFAULT_WEIGHTS) {}

  async score(_ctx: FeedContext, items: ScoredItem<Article>[]): Promise<void> {
    for (const s of items) {
      const c = s.components ?? {};
      s.score =
        (this.weights.read * (c.read ?? 0)) +
        (this.weights.like * (c.like ?? 0)) +
        (this.weights.share * (c.share ?? 0)) +
        (this.weights.skip * (c.skip ?? 0));
    }
  }
}
