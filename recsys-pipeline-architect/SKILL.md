---
name: recsys-pipeline-architect
description: >
  Designs composable recommendation, ranking, and feed pipelines using the
  six-stage Source→Hydrator→Filter→Scorer→Selector→SideEffect framework
  popularized by X's open-sourced For You algorithm. Use this skill when the
  user wants to build any system that picks "the top K items for a user/context"
  — content feeds, search ranking, task prioritization, notification ordering,
  RAG retrieval ranking, alert triage, ad selection. Produces a stage-by-stage
  spec, an interface definition in the user's target language, and a runnable
  scaffold. Triggers: "recommendation system", "feed algorithm", "ranking
  pipeline", "for you feed", "how should I rank X", "candidate pipeline",
  "content recommender", "pipeline architecture for recsys".
---

# recsys-pipeline-architect

A spec-and-scaffold skill for building **composable recommendation pipelines**.

Most "recommendation systems" in production are not exotic ML models — they
are *pipelines*: fetch candidates from one or more sources, enrich them with
metadata, filter the ineligible, score the rest, pick the top K, fire off
side effects. The pattern is universal. The implementation language and the
scoring function change; the pipeline shape does not.

This skill encodes that pattern as six composable stages, gives you the
trade-offs at each stage, and produces a working scaffold.

---

## When to invoke

The user is trying to answer one of these questions:

- "Given a user/query/context, which N items should I show, in what order?"
- "I have a feed. How do I make it personalized?"
- "I have a list of candidates from multiple sources. How do I merge and rank?"
- "I have a ranking scorer. How do I wrap it in proper pipeline plumbing?"
- "I want to swap my single 'relevance' score for multi-objective scoring."

If the user names a specific use case (Strapi content feed, RAG retrieval
ranking, task prioritizer, notification ordering, ad ranker, search results
reranker, etc.) — proceed. The pattern fits all of them.

If the user is asking about *model architecture* (transformer design, two-tower
retrieval, embedding training) — this is the wrong skill. This skill is about
*pipeline plumbing around* the model, not the model itself.

---

## The six-stage framework

Every pipeline this skill produces has these stages, in this order:

| # | Stage | Responsibility | Parallelizable? |
|---|---|---|---|
| 1 | **Source** | Fetch candidate items from one or more origins | Yes — multiple sources run in parallel |
| 2 | **Hydrator** | Enrich each candidate with the metadata needed for filtering and scoring | Yes — independent hydrators run in parallel |
| 3 | **Filter** | Drop candidates that should never be shown (blocked, expired, duplicate, ineligible) | Sequential — each filter sees fewer items |
| 4 | **Scorer** | Assign each surviving candidate one or more scores | Sequential — later scorers see earlier scores |
| 5 | **Selector** | Sort by final score, return top K | Single op |
| 6 | **SideEffect** | Cache, log, emit events, update served-history — anything non-blocking | Async — does not block the response |

### Why this exact order

- Sources before hydration: you want to know what candidates exist before paying to enrich them.
- Hydration before filtering: many filters need metadata (author info, age, subscription status) that the source did not provide.
- Filtering before scoring: scoring is the expensive stage. Drop the ineligible first.
- Scorer chain (not single scorer): real systems compose ML scoring + diversity reranking + business rules.
- Selector after scoring (not during): keeps scoring deterministic and cacheable.
- SideEffects last and async: side effects must never block the user response.

---

## Workflow when invoked

### Step 1: Clarify the use case (one round)

Ask the user (at most three questions, only what is missing):

1. **What are the items being ranked?** (posts, products, tasks, alerts, documents...)
2. **What is the input context?** (user ID, search query, current document, time window...)
3. **What language / runtime?** (TypeScript/Node, Go, Python, Rust...)

If the user already provided these, skip the questions and go directly to Step 2.

### Step 2: Identify the candidate sources

Most pipelines have at least two sources. Ask: "What pools of candidates exist?"

Common dual-source pattern:

- **In-network** — items directly connected to the user (followed, owned, subscribed, recent)
- **Out-of-network** — items the user has not seen but might want (ML retrieval, trending, similar-to-liked)

If the user only has one source, that is fine. The framework still applies — you just have a one-source pipeline.

### Step 3: List required hydrations

For each filter and scorer the user might want, ask "what data does this need that the source did not provide?" Each missing piece is a hydrator.

Common hydrators: core item metadata, author/owner profile, subscription/permission status, engagement counters, freshness/age, media presence.

### Step 4: List the filters

Filters are policy. They have nothing to do with relevance. They drop items that should never be shown to *this* user *now*.

Universal filter checklist (apply where relevant):

- **Duplicate filter** — same item ID twice in the candidate set
- **Self-filter** — items the user owns/authored
- **Age filter** — items older than threshold (or younger, for "fresh only")
- **Block/mute filter** — items from blocked owners, with muted keywords
- **Previously-served filter** — items already shown in this session
- **Eligibility filter** — paywall, geo-restriction, permission

Filter order matters: cheapest checks first.

### Step 5: Design the scorer chain

This is the heart of the pipeline. Recommend:

- **Primary scorer** — the ML model or scoring function that produces *per-action probabilities* or a relevance score
- **Combiner scorer** — turns multiple predictions into one final score via weighted sum
- **Diversity scorer** — attenuates repeated authors/categories to avoid feed monoculture
- **Business-rule scorer** — boosts/penalties from product (boost subscriptions, penalize sensitive topics)

The X For You algorithm uses 15 action probabilities (P(like), P(reply), P(repost), P(block), P(mute), P(report)...) combined with positive and negative weights. The skill explains this pattern in `references/multi-action-scoring.md` and recommends it when the user wants the optimization function to change without retraining.

### Step 6: Selector

Almost always: sort descending by final score, take top K. Variations: stratified selection (mix in-network and out-of-network at fixed ratio), positional debiasing (penalize position-1 if user does not engage).

### Step 7: SideEffects

Things that must happen after the response is sent, never blocking it:

- Cache the served item IDs for the "previously served" filter on next request
- Emit an impression event for downstream training data
- Update a per-user counter (rate limit, daily quota)
- Log for analytics

### Step 8: Generate the scaffold

Once the spec is clear, generate:

1. **The pipeline interface definitions** in the user's language (traits in Rust, interfaces in Go/TypeScript, ABCs in Python).
2. **A minimal runnable example** with one Source, one Hydrator, one Filter, one Scorer.
3. **A README.md** explaining how to add new stages.

Pick the example from `examples/` that matches the user's stack:

- `examples/strapi-content-feed/` — TypeScript/Node, Strapi v5 plugin shape
- `examples/zentra-go/` — Go, engine.Module interface compatible
- `examples/pmai-task-prioritizer/` — Python/FastAPI, async pipeline

If the user's stack does not match any of these, generate from scratch following the interfaces in `references/interfaces.md`.

---

## Key design decisions to surface

When generating the spec, the skill must surface these architectural choices to the user. These are not technical details; they are product decisions disguised as technical ones.

### 1. Single score or multi-action prediction?

- **Single score:** Simpler. Train one model to predict "relevance." When product wants to change behavior, retrain.
- **Multi-action:** Predict P(action) for many actions, combine with weights at serving time. To change behavior, change weights — no retraining.

The X For You system uses multi-action. The skill recommends multi-action when the user expects to tune frequently. See `references/multi-action-scoring.md`.

### 2. Candidate isolation in scoring?

- **Isolated:** Each candidate is scored independently. Score is deterministic and cacheable.
- **Joint:** Candidates can attend to each other during scoring (e.g., transformer over the whole batch). More expressive but non-deterministic across batches, harder to cache.

The X For You ranker uses candidate isolation via attention masking. The skill recommends isolation by default, joint only when there is a specific reason (e.g., explicit diversity-aware ranking that needs to see the full batch). See `references/candidate-isolation.md`.

### 3. Hand-engineered features or learned representations?

- **Hand-engineered:** Manual feature columns (item age, author follower count, engagement rates). Interpretable, fast iteration on new features.
- **Learned:** Pass raw engagement sequences to a transformer; let it learn its own features. The X For You system took this route and explicitly eliminated all hand-engineered features.

The skill does not recommend one over the other — both are valid in 2026. It surfaces the trade-off.

### 4. Where does the pipeline run?

- **Request-time (online):** Pipeline runs when the user asks for the feed. Latency budget: 100-300ms.
- **Pre-computed (offline batch):** Pipeline runs periodically, results cached. Latency: ms. Freshness: hours.
- **Hybrid:** Candidate retrieval offline, ranking online.

The default in this skill is request-time. Surface this decision to the user.

---

## Hard rules

1. **Do not invent benchmark numbers.** If the user asks "how much faster is X than Y?", say "depends on workload, run it yourself." Do not produce fabricated latency or throughput claims.

2. **Attribution discipline.** When the X For You algorithm pattern is referenced, attribute as "the pattern popularized by xAI's open-sourced For You algorithm" or "Apache 2.0 reference: github.com/xai-org/x-algorithm". Do not present the pattern as original to this skill.

3. **No trademark use.** Do not name the user's generated artifact "X-like" or use "For You" branding. The pattern is free to use; the brand is not. Suggested naming: "candidate pipeline", "feed pipeline", "ranking pipeline", "recsys pipeline".

4. **Surface trade-offs, do not hide them.** Multi-action vs single, isolation vs joint, online vs offline — these are real decisions. Never default silently.

5. **The generated scaffold must run.** No pseudocode passing as code. If the scaffold needs dependencies, install instructions are part of the output.

6. **Filter order matters.** Cheap before expensive. Universal before user-specific. Document this in the generated README.

7. **Side effects never block.** Generated code wraps side effects in fire-and-forget patterns (goroutines, promises without await, asyncio tasks). Document this.

---

## Reference files

Loaded on demand, not all upfront:

- `references/interfaces.md` — Pipeline interface definitions in TypeScript, Go, Python, Rust
- `references/multi-action-scoring.md` — Multi-action prediction pattern: when, how, weight tuning approach
- `references/candidate-isolation.md` — Attention masking pattern, cacheability argument, when to break the rule
- `references/filter-cookbook.md` — 12 common filters with implementation sketches
- `references/scorer-cookbook.md` — Scoring patterns: weighted sum, diversity penalty, MMR, position debiasing

---

## Example invocations

### Example 1: Strapi content feed
> "I'm running a Strapi v5 instance with 50k articles. I want a 'for you' feed personalized to each logged-in user based on their reading history."

→ Skill walks through the 8 steps, generates a Strapi plugin scaffold using `examples/strapi-content-feed/` as the template.

### Example 2: RAG retrieval reranker
> "My RAG returns top-50 chunks from a vector DB. I want to rerank them with a more expensive scorer and return top-5."

→ Skill recognizes this as a single-source pipeline with a scorer chain. Two-stage: cheap retrieval + expensive rerank is exactly the pattern. Generates a Python async pipeline.

### Example 3: Task prioritizer
> "PMAI receives a queue of incoming task suggestions. I want to rank them by 'what should this user work on next' considering their past patterns."

→ Skill recognizes this as recommendation with users-and-items reversed. Items are tasks, user context is engagement history. Generates a FastAPI scaffold.

### Example 4: Notification triage
> "We send too many notifications. I want a daily digest that picks the top 10 from the last 24h queue."

→ Skill identifies this as offline-batch pipeline. Generates a scheduled job scaffold.

---

## What this skill does NOT do

- Train ML models — the scoring function is your responsibility, the skill scaffolds where it plugs in
- Operate the deployed pipeline — no monitoring, no autoscaling decisions
- Predict pipeline performance — depends on your data, your hardware, your traffic
- Choose your vector DB / cache / queue — those are infrastructure decisions outside scope
- Write the marketing copy for your launch — different skill

---

## Compatibility

- **Claude.ai chat:** Direct invocation by use case description.
- **Claude Code:** Reads SKILL.md, generates files in the user's repo using create_file and view.
- **Codex / Gemini CLI / other CLI agents:** Markdown-based, vendor-agnostic. Reference files load progressively.

The skill is licensed MIT. The X For You algorithm patterns referenced are Apache 2.0, attributed in the generated scaffold's README.
