import { Pipeline } from '../pipeline/runner';
import { FeedContext, Article } from '../pipeline/types';
import { FollowingSource } from '../pipeline/sources/following';
import { SimilarToLikedSource } from '../pipeline/sources/similar-to-liked';
import { AuthorHydrator } from '../pipeline/hydrators/author';
import { EngagementCountsHydrator } from '../pipeline/hydrators/engagement-counts';
import {
  DuplicateFilter, SelfFilter, AgeFilter,
  BlockedAuthorFilter, AlreadyReadFilter,
} from '../pipeline/filters';
import { MultiActionScorer } from '../pipeline/scorers/multi-action';
import { WeightedSumCombiner } from '../pipeline/scorers/weighted-sum';
import { AuthorDiversityScorer } from '../pipeline/scorers/author-diversity';
import { TopKSelector } from '../pipeline/selectors/top-k';
import { MarkServedSideEffect } from '../pipeline/side-effects/mark-served';

export default ({ strapi }: { strapi: any }) => ({
  async forYou(userId: number, limit: number = 20) {
    const ctx = await this.buildContext(userId);

    const pipeline = new Pipeline<FeedContext, Article>({
      sources: [
        new FollowingSource(),
        new SimilarToLikedSource(),
      ],
      hydrators: [
        new AuthorHydrator(),
        new EngagementCountsHydrator(),
      ],
      filters: [
        new DuplicateFilter(),
        new SelfFilter(),
        new AgeFilter(),
        new BlockedAuthorFilter(),
        new AlreadyReadFilter(),
      ],
      scorers: [
        new MultiActionScorer(),
        new WeightedSumCombiner(),
        new AuthorDiversityScorer(),
      ],
      selector: new TopKSelector(),
      sideEffects: [
        new MarkServedSideEffect(),
      ],
    });

    return pipeline.run(ctx, limit);
  },

  async buildContext(userId: number): Promise<FeedContext> {
    // Replace these queries with your actual data model.
    // The example assumes relations: follows, blocks, likes, reads.
    const [follows, blocks, likes, reads] = await Promise.all([
      strapi.db.query('plugin::content-feed.follow').findMany({
        where: { followerId: userId },
        select: ['followingId'],
      }),
      strapi.db.query('plugin::content-feed.block').findMany({
        where: { blockerId: userId },
        select: ['blockedId'],
      }),
      strapi.db.query('plugin::content-feed.like').findMany({
        where: { userId },
        orderBy: { createdAt: 'desc' },
        limit: 100,
        populate: { article: { select: ['id', 'categorySlug'] } },
      }),
      strapi.db.query('plugin::content-feed.read').findMany({
        where: { userId },
        orderBy: { readAt: 'desc' },
        limit: 200,
        select: ['articleId'],
      }),
    ]);

    const followedAuthorIds = follows.map((f: any) => f.followingId);
    const blockedAuthorIds = blocks.map((b: any) => b.blockedId);
    const recentlyLikedArticleIds = likes.map((l: any) => l.article?.id).filter(Boolean);
    const recentlyReadArticleIds = reads.map((r: any) => r.articleId);

    // Derive preferred categories from like history
    const categoryCounts = new Map<string, number>();
    for (const l of likes as any[]) {
      const cat = l.article?.categorySlug;
      if (cat) categoryCounts.set(cat, (categoryCounts.get(cat) ?? 0) + 1);
    }
    const preferredCategories = [...categoryCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([cat]) => cat);

    return {
      userId,
      followedAuthorIds,
      blockedAuthorIds,
      recentlyLikedArticleIds,
      recentlyReadArticleIds,
      preferredCategories,
      strapi,
    };
  },
});
