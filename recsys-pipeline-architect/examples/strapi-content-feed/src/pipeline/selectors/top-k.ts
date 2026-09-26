import { Selector, ScoredItem } from '../interfaces';
import { FeedContext, Article } from '../types';

export class TopKSelector implements Selector<FeedContext, Article> {
  name = 'top_k';
  select(_ctx: FeedContext, items: ScoredItem<Article>[], k: number): ScoredItem<Article>[] {
    return [...items]
      .sort((a, b) => b.score - a.score)
      .slice(0, k);
  }
}
