# Research log — CPC/text extension

## Decision 1

**Observation:** The preceding analysis found Qualcomm denominator expansion and NVIDIA ML growth.

**Hypothesis:** Technology composition can distinguish substantive portfolio changes from label-only changes.

**Decision:** Enrich Qualcomm 2021/2023 and NVIDIA 2014–2016/2021–2023 grants.

**Justification:** These directly match the two findings requested for investigation; NVIDIA windows have equal three-year duration.

**Result:** 7,813 supplied grant rows selected; 263,602 source rows outside the extension scope, not deleted from the original analysis.

**Limitation:** This extension cannot locate the precise transition year between NVIDIA windows.

**Reasonable alternatives:** Enrich every company/year; use intermediate years; use a probability sample.

## Decision 2

**Observation:** Official USPTO PatentsView bulk metadata was downloadable.

**Hypothesis:** A census avoids convenience-sample bias.

**Decision:** Download fixed December 2024 release and verify published MD5s; retain all target titles, abstracts and dates.

**Justification:** Public bulk inputs are reproducible and remove the need for random sampling.

**Result:** All 7,813 target grants have title, abstract and filing-date fields.

**Limitation:** Titles/abstracts are not a full reading of claims or specifications.

**Reasonable alternatives:** Stratified random sampling; Google Patents search exports; licensed commercial metadata.

## Decision 3

**Observation:** CPC is one-to-many and evolves over time.

**Hypothesis:** Reclassification may create apparent technology changes.

**Decision:** Use current codes from one snapshot; retain at-issue codes for sensitivity.

**Justification:** A common snapshot improves comparability without pretending classification history is stable.

**Result:** Current and at-issue interpretations broadly agree; paired NVIDIA check uses 742 early and 784 recent grants.

**Limitation:** At-issue codes absent for 267 early NVIDIA grants; three further grants excluded only from paired sensitivity because current codes absent.

**Reasonable alternatives:** At-issue-only analysis; IPC concordance; historical CPC scheme crosswalk.

## Decision 4

**Observation:** Communications codes overlap across subclasses.

**Hypothesis:** A simple membership partition can identify where the net non-AI increase lies.

**Decision:** Define communications-associated as any H04W/L/B/J/K/M code; each grant counted once in the partition.

**Justification:** The partition is exact, interpretable and does not sum overlapping subclass totals.

**Result:** Communications-associated increase 1,608 / total classifier-negative increase 1,617 = 99.4%.

**Limitation:** Association with communications is not an exclusive invention field or proof of a causal reason.

**Reasonable alternatives:** First-listed CPC; fractional subclass credit (also supplied); detailed CPC groups.

## Decision 5

**Observation:** Current CPC omits six reissues.

**Hypothesis:** Code absence is a metadata limitation, not an invalid patent.

**Decision:** Retain reissues, blank codes and a no-communications/no-current-code category.

**Justification:** Deleting unusual identifiers would miscount genuine grants.

**Result:** No patent rows removed; six missing current-CPC cases exported for review.

**Limitation:** A missing code must not be interpreted as absence of that technology.

**Reasonable alternatives:** Exclude reissues with explicit sensitivity; retrieve original-patent codes.

## Decision 6

**Observation:** Classifier-negative is operational, not biological/technical truth.

**Hypothesis:** Qualcomm composition accounting may depend on the AI cutoff.

**Decision:** Repeat the decomposition at 50, 86 and 93; repeat with inventional codes only.

**Justification:** This probes label and coding choices without selecting a cutoff for significance.

**Result:** Communications explain 98.6%–99.7% of the net negative-grant increase across 12 specifications.

**Limitation:** Threshold sensitivity does not validate AIPD recall or precision.

**Reasonable alternatives:** Human claim-based labels; probabilistic score weighting.

## Decision 7

**Observation:** Text phrases identify concrete themes but abstracts contain boilerplate.

**Hypothesis:** Specific technical terms, corroborated by CPC and title-only checks, are more useful than raw topic ranks.

**Decision:** Use disclosed regex phrase rules and separate exploratory bigram contrasts; no opaque topic model.

**Justification:** Raw phrase rankings include drafting phrases such as 'various examples', which are not technologies.

**Result:** Sidelink, learned methods and autonomy increase in both title-only and combined-text analyses.

**Limitation:** Rules are exploratory and may miss synonyms or mention background technologies.

**Reasonable alternatives:** NMF/LDA after boilerplate removal; embeddings with manual validation; blinded human coding.

## Decision 8

**Observation:** Ray-tracing and rendering have orthographic/stem variants.

**Hypothesis:** Exact wording choices can affect counts.

**Decision:** Match ray-tracing/ray tracing/raytracing stems and render*; freeze rules in text_rules.json.

**Justification:** These are reasonable spelling and morphology variants, chosen before the final tables rather than for significance.

**Result:** Ray-tracing matches 5→60; rendering 118→106; 56 of 60 recent ray-tracing grants are ML86-negative.

**Limitation:** A keyword does not prove the patented claim's principal technical contribution.

**Reasonable alternatives:** Exact-phrase counts; manual classification of graphics claims.

## Decision 9

**Observation:** Qualcomm grant dates are later than the activity described in filings.

**Hypothesis:** Expansion may be driven by prior filing cohorts or prosecution delays.

**Decision:** Add direct filing dates and grant lags; preserve unusual durations.

**Justification:** Timing is needed before attributing 2023 grants to 2023 innovation or strategy.

**Result:** 2,916 / 3,446 negative 2023 grants were filed in 2020–2021; lag median 2.12→2.30 years, mean almost unchanged.

**Limitation:** Only granted applications are observed; direct filing dates need not equal first priority.

**Reasonable alternatives:** All pre-grant filings; allowance/prosecution histories; earliest family priorities.

## Decision 10

**Observation:** NVIDIA ML-positive and non-ML counts both change.

**Hypothesis:** Share growth can reflect more positives and fewer negatives.

**Decision:** Use two-factor Shapley accounting, averaging both update orders.

**Justification:** Contributions add exactly and avoid choosing an arbitrary ordering.

**Result:** Qualcomm: positive-count contribution 3.26 pp, negative-count contribution -7.11 pp; NVIDIA: 22.99 pp and 5.58 pp.

**Limitation:** Accounting contributions are not causal treatment effects.

**Reasonable alternatives:** One-order counterfactual; log-odds decomposition; Kitagawa decomposition.

## Decision 11

**Observation:** Neural and vision/control evidence overlap in NVIDIA ML grants.

**Hypothesis:** An additive partition can describe most of the ML rise without double-counting.

**Decision:** Order explicit learning text, then vision/control evidence without such text, then remaining ML grants.

**Justification:** The hierarchy makes the accounting transparent; retain independent overlapping theme counts as well.

**Result:** Explicit learning category 0→177, vision/control without explicit learning 1→38, other 6→15; total 7→230.

**Limitation:** Category order changes attribution; 'vision/control' combines image/vision CPC, perception phrases and autonomous mentions.

**Reasonable alternatives:** Nonexclusive thematic prevalence; fractional multi-theme allocation.

## Decision 12

**Observation:** G06V recognition classifications were revised with transfers from G06K9.

**Hypothesis:** An isolated G06V trend can confuse scheme change with innovation.

**Decision:** Check a harmonized G06T/G06V/G06K9 union and paired current/issue records.

**Justification:** Official CPC revision notice documents reclassification; text corroboration is independent of code migration.

**Result:** Paired vision/pattern share increases 29.5%→50.0% current and 28.3%→48.9% at issue.

**Limitation:** This is a pragmatic union, not a complete historical CPC concordance.

**Reasonable alternatives:** Detailed revision crosswalk; IPC; exclude G06V and rely on text.

## Decision 13

**Observation:** The targeted rows are a finite census, selected after the preceding EDA.

**Hypothesis:** Population-style patent-independent p-values or confidence intervals would impose unsupported assumptions.

**Decision:** Use exact finite-cohort effects, threshold/snapshot checks and leave-one-quarter-out ranges; no new confirmatory tests.

**Justification:** Unknown patent families and a one-year Qualcomm cohort make conventional inference unjustified.

**Result:** Sidelink share change remains +9.68 to +10.67 pp; NVIDIA explicit-learning change +23.11 to +24.45 pp under quarter omission.

**Limitation:** Sensitivity ranges are not confidence intervals; these results do not generalize to unobserved inventions.

**Reasonable alternatives:** Family-clustered inference after family linkage; prespecified replication period; temporal bootstrap with validated assumptions.

## Decision 14

**Observation:** Ten recent NVIDIA grants explicitly mention learned methods but fall below ML86.

**Hypothesis:** Some disagreement reflects component boundaries, text scope or model error.

**Decision:** Export all ten; inspect a linked accelerator case using original patent pages.

**Justification:** Anomalies inform interpretation and should not be deleted or automatically relabeled.

**Result:** Nine remain any-AI86-positive. Three linked same-title accelerator grants have ML scores 0.000484, 0.999996, 0.003449; all hardware86-positive.

**Limitation:** This does not establish a specific classifier error mechanism; claims differ and same-title patents can be distinct.

**Reasonable alternatives:** Expert claims adjudication; full AIPD inference-input audit; broader family study.