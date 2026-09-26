# Filter Cookbook

Twelve common filters. Each has a "why," a sketch, and a placement note.

Filters run sequentially. Order by cost: cheap, deterministic checks first. Expensive or network-bound checks last.

---

## 1. DuplicateFilter

**Why:** Multiple sources can return the same item. Score it once, show it once.

```typescript
class DuplicateFilter implements Filter<Ctx, Item> {
  name = "duplicate";
  private seen = new Set<string>();
  predicate(_ctx: Ctx, item: Item): boolean {
    const id = item.id;
    if (this.seen.has(id)) return false;
    this.seen.add(id);
    return true;
  }
}
```

**Placement:** First. Cheapest possible check.

---

## 2. SelfFilter

**Why:** Users should not see their own items in a "for you" feed (with some exceptions: in a search feed, they should).

```typescript
class SelfFilter implements Filter<{userId: string}, {authorId: string}> {
  name = "self";
  predicate(ctx, item) { return item.authorId !== ctx.userId; }
}
```

**Placement:** Early. Cheap.

---

## 3. AgeFilter

**Why:** Posts older than N hours/days are not relevant for a real-time feed.

```typescript
class AgeFilter implements Filter<Ctx, {createdAt: Date}> {
  name = "age";
  constructor(private maxAgeMs: number) {}
  predicate(_ctx, item) {
    return Date.now() - item.createdAt.getTime() < this.maxAgeMs;
  }
}
```

**Placement:** Early. Cheap. Threshold depends on use case (news: hours; evergreen content: weeks).

---

## 4. BlockedAuthorFilter

**Why:** Users explicitly told us never to show items from these authors.

```typescript
class BlockedAuthorFilter implements Filter<{blockedAuthorIds: Set<string>}, {authorId: string}> {
  name = "blocked_author";
  predicate(ctx, item) { return !ctx.blockedAuthorIds.has(item.authorId); }
}
```

**Placement:** Before scoring. The user has explicitly opted out.

---

## 5. MutedAuthorFilter

**Why:** Soft block. Same logic as BlockedAuthorFilter but different stored list.

```typescript
class MutedAuthorFilter implements Filter<{mutedAuthorIds: Set<string>}, {authorId: string}> {
  name = "muted_author";
  predicate(ctx, item) { return !ctx.mutedAuthorIds.has(item.authorId); }
}
```

**Placement:** Same as blocked.

---

## 6. MutedKeywordFilter

**Why:** Users specified keywords they never want to see ("politics", "spoilers", a specific show name).

```typescript
class MutedKeywordFilter implements Filter<{mutedKeywords: string[]}, {text: string}> {
  name = "muted_keyword";
  predicate(ctx, item) {
    const text = item.text.toLowerCase();
    return !ctx.mutedKeywords.some(kw => text.includes(kw.toLowerCase()));
  }
}
```

**Placement:** Before scoring. Cost depends on number of keywords × text length.

For >100 keywords, build an Aho-Corasick automaton once and reuse.

---

## 7. PreviouslySeenFilter

**Why:** Don't show items the user has already seen in past sessions. Requires persistent storage.

```typescript
class PreviouslySeenFilter implements Filter<{seenItemIds: Set<string>}, Item> {
  name = "previously_seen";
  predicate(ctx, item) { return !ctx.seenItemIds.has(item.id); }
}
```

**Placement:** Before scoring. Storage strategy: per-user Bloom filter for scale, or a Redis set with TTL.

---

## 8. PreviouslyServedFilter

**Why:** Within a single session (multiple feed refreshes), don't serve the same item twice.

```typescript
class PreviouslyServedFilter implements Filter<{servedThisSession: Set<string>}, Item> {
  name = "previously_served";
  predicate(ctx, item) { return !ctx.servedThisSession.has(item.id); }
}
```

**Placement:** Before scoring. SideEffect at the end of the pipeline writes to this set.

---

## 9. SubscriptionFilter

**Why:** Some items are paywalled. The user must have the subscription to see them.

```typescript
class SubscriptionFilter implements Filter<{userTier: string}, {requiredTier?: string}> {
  name = "subscription";
  predicate(ctx, item) {
    if (!item.requiredTier) return true;
    return ctx.userTier === item.requiredTier || ctx.userTier === "premium";
  }
}
```

**Placement:** Before scoring. Saves you from scoring items the user can't see.

---

## 10. GeoFilter

**Why:** Some items are geo-restricted (legal, licensing).

```typescript
class GeoFilter implements Filter<{country: string}, {restrictedCountries?: string[]}> {
  name = "geo";
  predicate(ctx, item) {
    return !item.restrictedCountries?.includes(ctx.country);
  }
}
```

**Placement:** Before scoring. Compliance requirement.

---

## 11. VisibilityFilter (Post-Selection)

**Why:** Items that became unavailable between scoring and serving — deleted, spam-flagged, violence/gore detected. Check this *after* selection (cheaper to run on K items than on the full candidate set).

```typescript
class VisibilityFilter implements Filter<Ctx, {visibilityStatus: string}> {
  name = "visibility";
  predicate(_ctx, item) {
    return item.visibilityStatus === "visible";
  }
}
```

**Placement:** Post-selector. This is the only filter that runs *after* selection rather than before.

---

## 12. RateLimitFilter

**Why:** Even if scoring loves this item, the user has seen too many items from this author/topic in the recent feed. Throttle.

```typescript
class RateLimitFilter implements Filter<{recentAuthorCounts: Map<string, number>}, {authorId: string}> {
  name = "rate_limit";
  constructor(private maxPerAuthor: number) {}
  predicate(ctx, item) {
    const count = ctx.recentAuthorCounts.get(item.authorId) || 0;
    return count < this.maxPerAuthor;
  }
}
```

**Placement:** Late, after scoring but before selection. (Some implementations do this in the selector instead; either works.)

---

## Filter ordering principle

```
Cost rises →
Cheap deterministic   → Cheap stateful   → Network-bound  → Expensive ML
(duplicate, self,        (blocked, muted,    (subscription,   (toxicity classifier,
 age)                     keyword)            geo)             quality model)
```

If your scoring uses an ML model that already learned to suppress low-quality content (e.g., it learned that P(report) is high → score is low), you may not need explicit quality filters. The X For You system relies heavily on this — quality is in the model, not in filters.

If you don't trust your model that much, add explicit filters as guardrails. Either approach is defensible.
