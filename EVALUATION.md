# Evaluation

## Method

Each skill pack was tested against hand-crafted sample datasets with intentionally planted
anomalies (known in advance), then verified whether CoreMind's Isolation Forest correctly
flagged those specific rows. This is a targeted correctness check rather than a large-scale
benchmark, appropriate for a hackathon-scale prototype with synthetic data.

## Results

**Sentinel (network logs)**
- Test data: 15 log entries with 3 intentionally injected anomalies (latency spikes with high
  packet loss and elevated device temperature).
- Result: 3/3 planted anomalies correctly flagged as the top anomaly_score entries, with no
  normal entries misflagged.

**FinSight (financial transactions)**
- Test data: transaction sets with a planted large, off-hours, repeated-merchant charge
  (₹45,000 / ₹38,000 / ₹55,000 across different test runs, all at 2-4 AM to "Unknown Merchant").
- Result: the planted anomaly was correctly flagged as the top anomaly in every run.

**StudyMate (study performance)**
- Test data: 8-9 topics with 2 intentionally low-scoring topics (e.g. Dynamic Programming at
  38%, Recursion at 42%).
- Result: initial version correctly flagged the low-scoring topics, but also flagged a
  legitimately high-scoring topic (Linked Lists, 90%) as anomalous — see Known Failure Cases.
  After adding a "below the student's own average" filter to the feature extractor, this false
  positive was eliminated in re-testing.

**HealthGuard (health vitals)**
- Test data: 8 days of vitals with 2 planted abnormal readings (elevated resting heart rate +
  low sleep hours).
- Result: both planted anomalies correctly flagged.

## Baseline Comparison

A simple fixed-threshold rule (e.g. "flag amount > ₹10,000" for FinSight, or "flag latency >
300ms" for Sentinel) would also catch the most obvious planted anomalies in each single-feature
case. The advantage of Isolation Forest over this baseline is that it considers multiple
features jointly — e.g. FinSight's detection also incorporates merchant frequency and hour of
day together, not just transaction amount alone, which would catch a moderately-sized but
oddly-timed repeated charge that a single-threshold rule on amount would miss entirely.

The tradeoff: Isolation Forest can also flag *statistically* unusual entries that aren't
*meaningfully* unusual for the domain (see the Linked Lists case below), whereas a hand-tuned
threshold rule would not have this failure mode — but a threshold rule also can't adapt to a
new domain without being manually rewritten, which the Isolation Forest approach handles for
free across all four skill packs.

## Known Failure Cases

1. **StudyMate false positive (fixed)**: A topic scoring 90% (the student's best subject) was
   initially flagged as anomalous purely because it was statistically different from the
   dataset's middling scores — Isolation Forest flags outliers in either direction. Since a
   study assistant should only ever flag *weak* spots, we added a domain-specific filter
   (`feature_extractor.py` only considers topics scoring below the student's own average) to
   eliminate this class of false positive entirely.

2. **LLM hallucination (mitigated, not eliminated)**: The local LLM (`phi3:mini`) occasionally
   invents small details not present in the input data (e.g. once claimed "only one answer was
   correct after all tries" when no such count existed in the input). This was mitigated by (a)
   lowering generation temperature to 0.2, (b) explicitly instructing the model not to invent
   facts beyond the given data, and (c) moving all actionable "fix" suggestions to a
   deterministic, human-written remediation-rules table that the LLM only rephrases rather than
   generates freely. This reduces but does not fully eliminate the risk of minor phrasing
   inaccuracies in the free-form explanation text, which is disclosed in the README's Known
   Limitations section.

3. **Small sample sizes**: All testing used synthetic datasets of 8-15 rows per skill pack.
   Isolation Forest's behavior on much larger or more diverse real-world datasets has not been
   validated in this project's timeframe, and the `contamination` parameter (currently static
   per skill) may need re-tuning for datasets of different sizes.
