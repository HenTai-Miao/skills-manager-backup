export default ({ strapi }: { strapi: any }) => ({
  async forYou(ctx: any) {
    const user = ctx.state?.user;
    if (!user) {
      return ctx.unauthorized('Authentication required');
    }

    const limit = Math.min(parseInt(ctx.query?.limit, 10) || 20, 100);

    const results = await strapi
      .plugin('content-feed')
      .service('feed')
      .forYou(user.id, limit);

    return {
      data: results.map((r: any) => ({
        id: r.item.id,
        documentId: r.item.documentId,
        title: r.item.title,
        author: {
          id: r.item.authorId,
          name: r.item.authorName,
          avatar: r.item.authorAvatar,
        },
        publishedAt: r.item.publishedAt,
        score: r.score,
        components: r.components,
      })),
      meta: { count: results.length },
    };
  },
});
