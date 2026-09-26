# Multi-Action Scoring

The most important architectural decision in a recommendation pipeline is *what the scorer outputs*.

## The single-score approach

The traditional approach: train a model to predict one number, "relevance" or "engagement probability." Sort by it.

```
score = model.predict(user, item)
```

Pros: simple to train, simple to serve, simple to debug.
Cons: every product change requires retraining. "We want to surface more video" → retrain. "We want to suppress political content" → retrain. "We're getting too many low-quality replies in the mix" → retrain.

## The multi-action approach

Predict probabilities for *many* user actions, combine at serving time via weighted sum.

```
predictions = model.predict(user, item)
# predictions = { 'like': 0.12, 'reply': 0.03, 'repost': 0.01,
#                 'click': 0.18, 'dwell': 0.41, 'mute': 0.001,
#                 'block': 0.0001, 'report': 0.00005, ... }

score = sum(weights[action] * predictions[action] for action in predictions)
```

The weights live outside the model. Changing product behavior is a config push, not a retrain.

The X For You algorithm uses this pattern. Their action set, from the open-sourced repo:

```
P(favorite)
P(reply)
P(repost)
P(quote)
P(click)
P(profile_click)
P(video_view)
P(photo_expand)
P(share)
P(dwell)
P(follow_author)
P(not_interested)
P(block_author)
P(mute_author)
P(report)
```

15 actions. Positive actions (favorite, reply, repost, quote, click, dwell, share, follow) get positive weights. Negative actions (not_interested, block, mute, report) get negative weights.

The interpretation flips. A single-score model asks "will the user engage?" A multi-action model asks "will the user be glad or sorry they saw this?"

## When to use multi-action

Recommend multi-action when:

- **Product roadmap is uncertain.** You'll be tuning the feed mix often.
- **There are clear "bad" actions you can observe.** Blocks, mutes, reports are negative training signal.
- **You have multiple stakeholders.** Editorial wants more long-form, growth wants more clicks, safety wants fewer reports. Weights become the negotiation surface.
- **Dwell or other passive signals matter.** Single-score systems struggle to combine dwell (passive) with reply (active).

Recommend single-score when:

- **You have one clear goal you'll never change.** Search-result relevance for a click-only product.
- **You don't have action telemetry yet.** You can only observe clicks. Then "P(click)" is your single score.
- **Your model is small and retraining is cheap.** Multi-action overhead isn't justified.

## How to pick weights

This is product work, not ML work. Weights are negotiated between teams. A reasonable starting point:

```
weights = {
    # Strong positive: explicit engagement
    'favorite': 0.5,
    'repost': 1.0,        # repost = "I want others to see this"
    'reply': 0.3,
    'quote': 0.4,

    # Moderate positive: implicit engagement
    'click': 0.1,
    'dwell': 0.2,         # dwell scaled by seconds, normalized
    'share': 1.0,         # DM share = strong signal

    # Strong positive: directional intent
    'follow_author': 2.0, # follow = "I want more from this person"

    # Strong negative
    'not_interested': -1.0,
    'mute_author': -3.0,
    'block_author': -10.0,
    'report': -20.0,
}
```

These are illustrative starting values, not benchmarks. Tune against your A/B testing infrastructure.

## Calibration

If your model outputs probabilities, they need to be calibrated (Platt scaling, isotonic regression) so the weighted sum is meaningful. An uncalibrated P(like) of 0.5 from one model is not comparable to P(reply) of 0.5 from another.

Calibration belongs in the scorer chain, after the primary ML scorer:

```
[PrimaryMLScorer] → [CalibrationScorer] → [WeightedSumCombiner] → [DiversityScorer]
```

## The product-engineering bonus

Multi-action scoring decouples model training from product decisions. The model team owns: "predict these N actions as accurately as possible." The product team owns: "how do we combine them this quarter?"

This separation is more valuable than the recommendation quality improvement, in most organizations.
