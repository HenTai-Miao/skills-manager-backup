// Shared types for the feed pipeline

export interface FeedContext {
  userId: number;
  followedAuthorIds: number[];
  blockedAuthorIds: number[];
  recentlyLikedArticleIds: number[];
  recentlyReadArticleIds: number[];
  preferredCategories: string[]; // populated from like history
  strapi: any; // Strapi instance
}

export interface Article {
  id: number;
  documentId: string;
  title: string;
  authorId: number;
  categorySlug: string;
  publishedAt: Date;
  // hydrated:
  authorName?: string;
  authorAvatar?: string;
  readCount?: number;
  likeCount?: number;
  // source tag for OON penalty
  source?: 'following' | 'similar_to_liked';
}
