# Strapi Content Feed Example

A Strapi v5 plugin shape that adds a personalized "for you" feed endpoint to any Strapi instance with an `article` content type.

This is an example scaffold the `recsys-pipeline-architect` skill generates. It is not a published Strapi plugin (yet). Use it as a template, customize per your content model.

## What it does

Adds `GET /api/feed/for-you` to your Strapi instance. Returns top 20 articles personalized to the authenticated user, based on:

- Articles from authors the user follows (in-network source)
- Articles similar to ones the user has previously liked (out-of-network source, using a simple cosine similarity over category vectors — replace with a real embedding model in production)
- Multi-action scoring: P(read), P(like), P(share), P(skip) combined with weights
- Author diversity penalty
- Standard filters: blocked authors, already-read, age cap of 30 days

## Files

```
strapi-content-feed/
├── README.md                          # this file
├── package.json
├── tsconfig.json
├── src/
│   ├── plugin.ts                      # plugin entry
│   ├── pipeline/
│   │   ├── interfaces.ts              # the six pipeline interfaces
│   │   ├── runner.ts                  # the Pipeline class
│   │   ├── sources/
│   │   │   ├── following.ts
│   │   │   └── similar-to-liked.ts
│   │   ├── hydrators/
│   │   │   ├── author.ts
│   │   │   └── engagement-counts.ts
│   │   ├── filters/
│   │   │   ├── duplicate.ts
│   │   │   ├── self.ts
│   │   │   ├── age.ts
│   │   │   ├── blocked-author.ts
│   │   │   └── already-read.ts
│   │   ├── scorers/
│   │   │   ├── multi-action.ts
│   │   │   ├── weighted-sum.ts
│   │   │   └── author-diversity.ts
│   │   ├── selectors/
│   │   │   └── top-k.ts
│   │   └── side-effects/
│   │       └── mark-served.ts
│   ├── controllers/
│   │   └── feed.ts
│   ├── routes/
│   │   └── feed.ts
│   └── services/
│       └── feed.ts
└── tests/
    └── pipeline.test.ts
```

## Installing into a Strapi v5 project

```bash
# From your Strapi project root
cd src/plugins
git clone <this-folder> content-feed
cd content-feed
npm install
```

Add to `config/plugins.ts`:

```typescript
export default {
  'content-feed': {
    enabled: true,
    resolve: './src/plugins/content-feed',
  },
};
```

Restart Strapi.

## Usage

```bash
curl -H "Authorization: Bearer $JWT" \
  http://localhost:1337/api/feed/for-you?limit=20
```

Response:

```json
{
  "data": [
    {
      "id": 42,
      "documentId": "abc123",
      "title": "...",
      "score": 0.847,
      "components": {
        "read": 0.61,
        "like": 0.18,
        "share": 0.04,
        "skip": 0.02,
        "diversity_penalty": 1.0
      }
    },
    ...
  ],
  "meta": { "count": 20 }
}
```

## Customizing the scoring weights

Weights live in `config/feed-weights.ts`. Edit and restart:

```typescript
export default {
  read: 1.0,
  like: 2.0,
  share: 3.0,
  skip: -1.0,
  block_author: -10.0,
};
```

No retraining. No deploy if you load weights via the config service.

## Replacing the placeholder ML scorer

The example uses a trivial scorer (category overlap with the user's liked articles). To plug in a real model:

1. Train a model that predicts P(read), P(like), P(share), P(skip) per (user, article) pair.
2. Serve it via HTTP or local inference.
3. Replace `src/pipeline/scorers/multi-action.ts` with a client that calls your model.

The pipeline plumbing stays the same.

## Attribution

The six-stage pipeline pattern (Source → Hydrator → Filter → Scorer → Selector → SideEffect) is inspired by xAI's open-sourced X For You algorithm, released under Apache 2.0:
https://github.com/xai-org/x-algorithm

This example reimplements the pattern from scratch in TypeScript. No code is copied from the original repo.

## License

MIT.
