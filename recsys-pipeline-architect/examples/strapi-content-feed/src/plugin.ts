import controllers from './controllers/feed';
import routes from './routes/feed';
import services from './services/feed';

export default {
  register() {},
  bootstrap() {},
  destroy() {},
  config: {
    default: {
      weights: {
        read: 1.0,
        like: 2.0,
        share: 3.0,
        skip: -1.0,
      },
      diversityDecay: 0.5,
      maxArticleAgeMs: 30 * 24 * 60 * 60 * 1000,
    },
    validator() {},
  },
  controllers: {
    feed: controllers,
  },
  routes,
  services: {
    feed: services,
  },
};
