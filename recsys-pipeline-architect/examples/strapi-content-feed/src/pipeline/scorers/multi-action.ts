import { Scorer, ScoredItem } from '../interfaces';
import { FeedContext, Article } from '../types';

/**
 * Placeholder multi-action predictor.
 *
 * In production, replace with a call to your ML model.
 * The interface is: given (user_context, article), output action probabilities.
 *
 * This stub computes pseudo-probabilities from cheap heuristics:
 *  - P(read): freshness + author affinity
 *  - P(like): category overlap + author affinity
 *  - P(share): like count signal
 *  - P(skip): age decay
 *
 * It's enough to make the pipeline runnable end-to-end. Replace before
 * shipping to anyone.
 */
export class MultiActionScorer implements Scorer<FeedContext, Article> {
  name = 'multi_action_predictor';

  async score(ctx: FeedContext, items: ScoredItem<Article>[]): Promise<void> {
    for (const s of items) {
      const a = s.item;
      const ageDays = (Date.now() - a.publishedAt.getTime()) / 86_400_000;
      const followedAuthor = ctx.followedAuthorIds.includes(a.authorId) ? 1 : 0;
      const categoryMatch = ctx.preferredCategories.includes(a.categorySlug) ? 1 : 0;

      // Decaying freshness signal
      const freshness = Math.exp(-ageDays / 7);

      const pRead = clamp01(0.3 * freshness + 0.4 * followedAuthor + 0.2 * categoryMatch);
      const pLike = clamp01(0.2 * categoryMatch + 0.3 * followedAuthor + 0.05 * Math.log1p(a.likeCount ?? 0));
      const pShare = clamp01(0.02 * Math.log1p(a.likeCount ?? 0));
      const pSkip = clamp01(0.5 * (1 - freshness));

      s.components = {
        read: pRead,
        like: pLike,
        share: pShare,
        skip: pSkip,
      };
    }
  }
}

function clamp01(x: number): number {
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
}
