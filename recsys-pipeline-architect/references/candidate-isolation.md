# Candidate Isolation

A subtle but important architectural decision in transformer-based scoring.

## The pattern

When you score a batch of N candidate items for a user, the question is: *can each candidate's representation attend to the other candidates in the batch, or only to the user context?*

**Candidate isolation:** Each candidate attends only to user context. The score for item X depends on (user, X) — not on what else is in the batch.

**Joint scoring:** Each candidate can attend to other candidates. The score for item X depends on (user, X, all_other_candidates_in_batch).

The X For You ranker uses candidate isolation. From their docs:

> Uses special attention masking so candidates cannot attend to each other.

## Why isolation matters

### 1. Cacheability

If `score(user, X)` depends only on `user` and `X`, the score can be cached. The next time the system sees the same (user, X) pair within the cache TTL, no model call needed.

If `score(user, X, batch)` depends on the batch, the cache key has to include the full batch, which never repeats — the cache is useless.

For a system serving billions of feed requests per day, this matters at the infra level. Cache hit rate on candidate scoring is often 30-60% in well-isolated systems.

### 2. Determinism

With isolation, identical inputs produce identical scores. Bug reports become reproducible. A/B test results become stable. Debugging is possible.

With joint scoring, the score depends on which other candidates happened to be in the batch — which depends on retrieval randomness, system load, parallelism. The same user can see different feeds on reload.

### 3. Composability

Isolated scorers are pure functions. You can stack them, swap them, parallelize them.

Joint scorers are not. They must see the whole batch. They cannot be naively parallelized across candidates.

## When to break isolation

Sometimes joint scoring is the right answer:

### Diversity-aware ranking

Maximal Marginal Relevance (MMR) and listwise rerankers explicitly trade off relevance against difference from already-selected items. They must see the batch.

Solution: keep the primary scorer isolated, do diversity as a separate selector or scorer stage that sees the full batch. The X For You system does exactly this — diversity is a separate "AuthorDiversityScorer" stage after the isolated transformer.

### Whole-page optimization

If you're ranking for a UI with positional constraints (sponsored slots, must-include items, layout rules), the scoring needs to be joint with the layout.

Solution: still keep the candidate scorer isolated. Run the joint optimization as a final selector stage on top of isolated per-item scores.

### Cross-candidate signals

If you genuinely need item-to-item information (e.g., a recommendation explicitly explained by "people who liked X also liked Y"), you might score pairs.

Solution: this is usually better modeled as a retrieval step, not a ranking step. Retrieve the "also liked Y" candidates as a separate source.

## The mask

In a transformer, isolation is enforced via the attention mask. The mask says "candidate token i cannot attend to candidate token j when i != j."

Schematic:

```
User context tokens:  [u1, u2, u3, ..., uN]
Candidate tokens:     [c1, c2, c3, ..., cM]

Attention mask:
  ui can attend to: all uj (full self-attention on user context)
  ci can attend to: all uj (read user context)
                    ci itself
                    NOT cj for j != i
```

In code (PyTorch sketch):

```python
def build_isolation_mask(n_user_tokens: int, n_candidate_tokens: int) -> torch.Tensor:
    total = n_user_tokens + n_candidate_tokens
    mask = torch.zeros(total, total, dtype=torch.bool)

    # User tokens attend to other user tokens
    mask[:n_user_tokens, :n_user_tokens] = True

    # Candidate tokens attend to user tokens
    mask[n_user_tokens:, :n_user_tokens] = True

    # Each candidate attends to itself, not other candidates
    for i in range(n_candidate_tokens):
        idx = n_user_tokens + i
        mask[idx, idx] = True

    return mask  # True = can attend
```

## The default

This skill recommends isolation by default. Break it only when you have a specific listwise reason, and break it in a separate stage (selector or diversity scorer) — not in the primary scorer.

The argument is not "joint scoring is bad." The argument is "isolation is the default that buys you cacheability, determinism, and composability for free. Pay for joint scoring only where you must."
