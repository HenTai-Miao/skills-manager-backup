import { Source } from '../interfaces';
import { FeedContext, Article } from '../types';

/**
 * Out-of-network source: articles in categories the user has liked,
 * NOT from authors they follow (so it's truly "discovery"), recent.
 *
 * This is a placeholder. In production, replace with embedding-based
 * similarity over user-history and candidate-article vectors.
 */
export class SimilarToLikedSource implements Source<FeedContext, Article> {
  name = 'similar_to_liked';
  constructor(private readonly limit: number = 50) {}

  async fetch(ctx: FeedContext): Promise<Article[]> {
    if (ctx.preferredCategories.length === 0) return [];

    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

    const results = await ctx.strapi.documents('api::article.article').findMany({
      filters: {
        category: { slug: { $in: ctx.preferredCategories } },
        author: { id: { $notIn: ctx.followedAuthorIds } },
        publishedAt: { $gte: sevenDaysAgo },
      },
      sort: { publishedAt: 'desc' },
      limit: this.limit,
      populate: ['author', 'category'],
    });

    return results.map((r: any) => ({
      id: r.id,
      documentId: r.documentId,
      title: r.title,
      authorId: r.author?.id,
      categorySlug: r.category?.slug ?? 'uncategorized',
      publishedAt: new Date(r.publishedAt),
      source: 'similar_to_liked' as const,
    }));
  }
}
