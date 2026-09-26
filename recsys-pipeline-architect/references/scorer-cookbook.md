# Scorer Cookbook

Six scoring patterns you compose into a chain. Each takes `ScoredItem[]` and mutates the `score` field (and optionally `components`).

The order matters: later scorers see earlier scores.

A typical chain:

```
[PrimaryMLScorer] → [CalibrationScorer] → [WeightedSumCombiner]
                  → [DiversityScorer]    → [BusinessRuleScorer]
                  → [OutOfNetworkPenaltyScorer]
```

---

## 1. PrimaryMLScorer

Calls the ML model. In the X For You pattern, this is the Grok-based transformer producing 15 action probabilities. In simpler systems, it's a single relevance score.

```typescript
class PrimaryMLScorer implements Scorer<Ctx, Item> {
  name = "primary_ml";
  constructor(private model: MLClient) {}
  async score(ctx, items) {
    const batch = items.map(s => ({ user: ctx, item: s.item }));
    const predictions = await this.model.batchPredict(batch);
    items.forEach((s, i) => {
      s.components = predictions[i]; // { like: 0.12, reply: 0.03, ... }
    });
    return items;
  }
}
```

This scorer doesn't set `score` directly — it populates `components`. The combiner does the math.

---

## 2. WeightedSumCombiner

Turns multi-action predictions into a single score.

```typescript
class WeightedSumCombiner implements Scorer<Ctx, Item> {
  name = "weighted_sum";
  constructor(private weights: Record<string, number>) {}
  async score(_ctx, items) {
    for (const s of items) {
      s.score = Object.entries(s.components || {})
        .reduce((acc, [action, p]) => acc + (this.weights[action] || 0) * p, 0);
    }
    return items;
  }
}
```

Weights are config, not code. Push them as environment variables or fetch from a flag service so you can tune without deploying.

---

## 3. DiversityScorer

Penalizes repeated authors/categories to avoid feed monoculture.

```typescript
class AuthorDiversityScorer implements Scorer<Ctx, {authorId: string}> {
  name = "author_diversity";
  constructor(private decayPerRepeat: number = 0.5) {}
  async score(_ctx, items) {
    // Sort by current score, then attenuate repeats
    const sorted = [...items].sort((a, b) => b.score - a.score);
    const seen = new Map<string, number>();
    for (const s of sorted) {
      const authorId = s.item.authorId;
      const repeatCount = seen.get(authorId) || 0;
      if (repeatCount > 0) {
        const multiplier = Math.pow(this.decayPerRepeat, repeatCount);
        s.score *= multiplier;
        s.components = { ...s.components, diversity_penalty: multiplier };
      }
      seen.set(authorId, repeatCount + 1);
    }
    return items;
  }
}
```

The decay rate is tunable. 0.5 means the 2nd item from the same author scores half; 3rd, a quarter; etc.

This is one of the few places where joint information (other candidates) is used. Keep this in its own stage so the primary scorer stays isolated.

---

## 4. BusinessRuleScorer

Boosts and penalties from product.

```typescript
class BusinessRuleScorer implements Scorer<Ctx, Item> {
  name = "business_rules";
  constructor(private rules: Rule[]) {}
  async score(ctx, items) {
    for (const s of items) {
      for (const rule of this.rules) {
        if (rule.matches(ctx, s.item)) {
          s.score *= rule.multiplier;
          s.components = {
            ...s.components,
            [`rule_${rule.name}`]: rule.multiplier
          };
        }
      }
    }
    return items;
  }
}
```

Examples of rules:
- "Boost items from subscribed creators by 1.2x"
- "Penalize items tagged 'sensitive' by 0.3x"
- "Boost items from this morning's editorial picks by 2.0x"

Keep rules data, not code. Stored in a config service, hot-reloadable.

---

## 5. OutOfNetworkPenaltyScorer

Out-of-network candidates (from ML retrieval, not from followed accounts) often have systematically higher scores because the retrieval already pre-filtered for engagement. Apply a constant penalty to make in-network and out-of-network comparable.

```typescript
class OONPenaltyScorer implements Scorer<Ctx, {source: string}> {
  name = "oon_penalty";
  constructor(private penalty: number = 0.7) {}
  async score(_ctx, items) {
    for (const s of items) {
      if (s.item.source === "out_of_network") {
        s.score *= this.penalty;
      }
    }
    return items;
  }
}
```

This is a calibration scorer. Tune the penalty by watching what fraction of the final feed is out-of-network and adjusting until it matches the product target.

---

## 6. PositionDebiasingScorer (optional)

If you serve a ranked list and observe that position-1 always gets clicks (the position bias), you can debias the predictions: discount predicted P(click) by an estimated position-bias function.

```typescript
class PositionDebiasingScorer implements Scorer<Ctx, Item> {
  name = "position_debias";
  constructor(private debiasFn: (rank: number) => number) {}
  async score(_ctx, items) {
    const sorted = [...items].sort((a, b) => b.score - a.score);
    sorted.forEach((s, rank) => {
      const factor = this.debiasFn(rank);
      s.score *= factor;
    });
    return items;
  }
}
```

This is advanced and typically only worth doing once you have enough traffic to estimate the position-bias curve from your own data.

---

## What goes in components

Every scorer that contributes to the final score should write to `components` for observability. When something looks wrong in production ("why is this post ranked 47th?"), you read `components` and see the breakdown.

```json
{
  "like": 0.12,
  "reply": 0.03,
  "repost": 0.01,
  "mute": 0.001,
  "diversity_penalty": 0.5,
  "rule_subscribed_creator": 1.2,
  "oon_penalty": 0.7
}
```

Storing components in production at high volume is expensive. Sample at 1% of requests, log the rest only on error or explicit debug request.

---

## What does NOT go in the scorer

- **Filters.** If you find yourself writing a scorer that returns -infinity for certain items, you actually want a filter.
- **Selection.** If you find yourself writing a scorer that needs to know the final K, you want logic in the selector, not the scorer.
- **Side effects.** Scorers should be pure functions. If you're emitting events from inside a scorer, move that to a SideEffect.

Stage discipline is what makes the framework work.
