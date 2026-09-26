export default {
  type: 'content-api',
  routes: [
    {
      method: 'GET',
      path: '/feed/for-you',
      handler: 'feed.forYou',
      config: {
        auth: { scope: ['authenticated'] },
        description: 'Personalized for-you feed for the authenticated user',
        tag: { plugin: 'content-feed', name: 'Feed' },
      },
    },
  ],
};
