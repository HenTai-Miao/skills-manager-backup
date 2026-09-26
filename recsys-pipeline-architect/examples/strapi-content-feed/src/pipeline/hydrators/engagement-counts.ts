import { Hydrator } from '../interfaces';
import { FeedContext, Article } from '../types';

/**
 * Enrich articles with aggregate engagement counts (reads, likes).
 * In production these come from a counter store (Redis), not the DB.
 */
export class EngagementCountsHydrator implements Hydrator<FeedContext, Article> {
  name = 'engagement_counts';

  async hydrate(ctx: FeedContext, items: Article[]): Promise<void> {
    if (items.length === 0) return;
    const articleIds = items.map(a => a.id);

    // Replace with your real counter store.
    // This stub queries Strapi's relations as a placeholder.
    const counts = await ctx.strapi.db.query('api::article.article').findMany({
      where: { id: { $in: articleIds } },
      select: ['id'],
      populate: { likes: { count: true }, reads: { count: true } },
    });

    const map = new Map<number, { likeCount: number; readCount: number }>();
    for (const c of counts as any[]) {
      map.set(c.id, {
        likeCount: c.likes?.count ?? 0,
        readCount: c.reads?.count ?? 0,
      });
    }

    for (const item of items) {
      const stats = map.get(item.id);
      if (stats) {
        item.likeCount = stats.likeCount;
        item.readCount = stats.readCount;
      }
    }
  }
}
