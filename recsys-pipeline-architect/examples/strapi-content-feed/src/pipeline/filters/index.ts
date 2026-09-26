import { Filter } from '../interfaces';
import { FeedContext, Article } from '../types';

export class DuplicateFilter implements Filter<FeedContext, Article> {
  name = 'duplicate';
  private seen = new Set<number>();
  keep(_ctx: FeedContext, item: Article): boolean {
    if (this.seen.has(item.id)) return false;
    this.seen.add(item.id);
    return true;
  }
}

export class SelfFilter implements Filter<FeedContext, Article> {
  name = 'self';
  keep(ctx: FeedContext, item: Article): boolean {
    return item.authorId !== ctx.userId;
  }
}

export class AgeFilter implements Filter<FeedContext, Article> {
  name = 'age';
  constructor(private readonly maxAgeMs: number = 30 * 24 * 60 * 60 * 1000) {}
  keep(_ctx: FeedContext, item: Article): boolean {
    return Date.now() - item.publishedAt.getTime() < this.maxAgeMs;
  }
}

export class BlockedAuthorFilter implements Filter<FeedContext, Article> {
  name = 'blocked_author';
  keep(ctx: FeedContext, item: Article): boolean {
    return !ctx.blockedAuthorIds.includes(item.authorId);
  }
}

export class AlreadyReadFilter implements Filter<FeedContext, Article> {
  name = 'already_read';
  keep(ctx: FeedContext, item: Article): boolean {
    return !ctx.recentlyReadArticleIds.includes(item.id);
  }
}
