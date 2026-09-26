import { Scorer, ScoredItem } from '../interfaces';
import { FeedContext, Article } from '../types';

/**
 * Attenuate scores for repeated authors so the feed doesn't get monopolized
 * by one prolific writer.
 *
 * decay = 0.5 means the 2nd item from an author gets half the score,
 * 3rd gets a quarter, etc.
 */
export class AuthorDiversityScorer implements Scorer<FeedContext, Article> {
  name = 'author_diversity';
  constructor(private readonly decayPerRepeat: number = 0.5) {}

  async score(_ctx: FeedContext, items: ScoredItem<Article>[]): Promise<void> {
    const sorted = [...items].sort((a, b) => b.score - a.score);
    const repeats = new Map<number, number>();

    for (const s of sorted) {
      const authorId = s.item.authorId;
      const count = repeats.get(authorId) ?? 0;
      if (count > 0) {
        const multiplier = Math.pow(this.decayPerRepeat, count);
        s.score *= multiplier;
        s.components = { ...s.components, diversity_penalty: multiplier };
      }
      repeats.set(authorId, count + 1);
    }
  }
}
