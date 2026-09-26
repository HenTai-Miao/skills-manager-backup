import { SideEffect, ScoredItem } from '../interfaces';
import { FeedContext, Article } from '../types';

/**
 * After we serve a feed, record which articles were served so we can
 * filter them out of the next refresh.
 *
 * Storage: per-user set in Redis (or whatever you wire up). This example
 * uses Strapi's built-in DB as a placeholder.
 */
export class MarkServedSideEffect implements SideEffect<FeedContext, Article> {
  name = 'mark_served';

  async emit(ctx: FeedContext, items: ScoredItem<Article>[]): Promise<void> {
    if (items.length === 0) return;
    const articleIds = items.map(s => s.item.id);
    // Fire-and-forget. Errors logged but never thrown to caller.
    try {
      await ctx.strapi.db.query('plugin::content-feed.served').createMany({
        data: articleIds.map(id => ({
          userId: ctx.userId,
          articleId: id,
          servedAt: new Date(),
        })),
      });
    } catch (err) {
      console.error('MarkServedSideEffect failed:', err);
    }
  }
}
