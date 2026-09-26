import { Hydrator } from '../interfaces';
import { FeedContext, Article } from '../types';

/**
 * Enrich articles with author display info.
 * The sources only fetched author ID; this populates name + avatar.
 */
export class AuthorHydrator implements Hydrator<FeedContext, Article> {
  name = 'author';

  async hydrate(ctx: FeedContext, items: Article[]): Promise<void> {
    if (items.length === 0) return;
    const authorIds = [...new Set(items.map(a => a.authorId).filter(Boolean))];
    if (authorIds.length === 0) return;

    const authors = await ctx.strapi.documents('plugin::users-permissions.user').findMany({
      filters: { id: { $in: authorIds } },
      fields: ['id', 'username', 'avatar'],
    });

    const authorMap = new Map(authors.map((a: any) => [a.id, a]));
    for (const item of items) {
      const author = authorMap.get(item.authorId);
      if (author) {
        item.authorName = (author as any).username;
        item.authorAvatar = (author as any).avatar;
      }
    }
  }
}
