import { Source } from '../interfaces';
import { FeedContext, Article } from '../types';

/**
 * In-network source: articles from authors the user follows,
 * published in the last 30 days.
 */
export class FollowingSource implements Source<FeedContext, Article> {
  name = 'following';
  constructor(private readonly maxPerAuthor: number = 5) {}

  async fetch(ctx: FeedContext): Promise<Article[]> {
    if (ctx.followedAuthorIds.length === 0) return [];

    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

    const results = await ctx.strapi.documents('api::article.article').findMany({
      filters: {
        author: { id: { $in: ctx.followedAuthorIds } },
        publishedAt: { $gte: thirtyDaysAgo },
      },
      sort: { publishedAt: 'desc' },
      limit: this.maxPerAuthor * ctx.followedAuthorIds.length,
      populate: ['author', 'category'],
    });

    return results.map((r: any) => ({
      id: r.id,
      documentId: r.documentId,
      title: r.title,
      authorId: r.author?.id,
      categorySlug: r.category?.slug ?? 'uncategorized',
      publishedAt: new Date(r.publishedAt),
      source: 'following' as const,
    }));
  }
}
