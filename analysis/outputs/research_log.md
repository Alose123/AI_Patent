# Research log: observations, decisions and limitations

## 01 — Stage 01

Observation: 271k-scale extract contains both AI and non-AI granted documents.

Hypothesis: Matched company portfolios may permit an AI share denominator.

Decision: Validate keys, flag-score rules, dates, and assignee mappings before deriving features.

Justification: Loading successfully is insufficient; denominator coverage and one-to-many joins are separate concerns.

Result: 271,415 rows; 271,414 patents; 0 hard integrity failures.

Limitation: Cannot calculate unmatched rates or corporate-group completeness without upstream inputs and merge code.

## 02 — Stage 01

Observation: A patent has IBM and Microsoft assignee records; RE identifiers appear.

Hypothesis: Repeated document and nonnumeric IDs may be legitimate rather than corrupt.

Decision: Retain shared memberships and valid reissues; check document metadata consistency.

Justification: Blind patent-ID deduplication would remove an ownership observation; removing RE would discard valid grants.

Result: 1 shared patent; 143 reissue rows.

Limitation: Parent patents and full co-assignee lists are unavailable; within-sample fractional weights are not full ownership fractions.

## 03 — Stage 01

Observation: USPTO corrected an earlier predict93 threshold issue in January 2025.

Hypothesis: This extract might contain the older 89.93% cutoff.

Decision: Compare every supplied flag with the score-based 50%, 86%, and 93% cutoffs.

Justification: A version anomaly can be diagnosed internally without replacing the dataset.

Result: Total threshold disagreements: 0.

Limitation: Passing rules does not authenticate the source release or assess classification accuracy.

## 04 — Stage 02

Observation: Only location_id has missing values; no core outcome/identity missingness.

Hypothesis: Geographic missingness need not invalidate company/time analysis.

Decision: Do not impute locations or delete their rows; keep all rows and source values.

Justification: Location is not required for the selected research estimands; dropping rows creates avoidable selection.

Result: 271,415 rows retained, 67 columns including derived features.

Limitation: Geographic analysis would require location joins and a separate missingness assessment.

## 05 — Stage 02

Observation: Earliest company records and small annual volumes differ substantially.

Hypothesis: Lifetime pooling may confuse company age and portfolio composition with company differences.

Decision: Use 2010-2023 annual shares as main comparison, retain full history for coverage EDA.

Justification: All five have >=100 documents each year in this window; alternative 2009-2023 or 2014-2023 windows are possible.

Result: 197,816 patent-company records in main period.

Limitation: This is an observed-coverage choice, not evidence that the corporate portfolios are complete.

## 06 — Stage 02

Observation: Classifier supplies eight overlapping technology labels.

Hypothesis: A broad any-AI trend could be driven by hardware alone or by multiple technology areas.

Decision: Derive nonhardware, hardware-only, component-count and threshold-borderline diagnostics.

Justification: These preserve multilabel structure; mutually exclusive categories would discard overlap.

Result: Features defined in derived_variable_dictionary.csv; original flags unchanged.

Limitation: Knowledge processing/planning/hardware remain broad historical classifier categories; these are not generative-AI labels.

## 07 — Stage 03

Observation: Counts and proportions change differently; several large annual volume jumps occur.

Hypothesis: A lower AI count may reflect portfolio contraction rather than declining AI concentration.

Decision: Show both metrics and decompose 2021-2023 count changes symmetrically.

Justification: Counts measure grant output; shares condition on captured portfolio size; the identity avoids attributing mix effects to volume.

Result: See annual metrics, anomaly flags, and count_share_decomposition.csv; no outlier rows removed.

Limitation: The decomposition is arithmetic, not causal; changes in capture and patenting strategy remain possible.

## 08 — Stage 03

Observation: Recent technology profiles and early-to-recent contrasts show company differences.

Hypothesis: Machine learning share may rise despite a flat broad any-AI share; NVIDIA may shift from hardware/vision toward ML.

Decision: Freeze 10 exploratory primary tests: five company slopes for any AI and five for ML at 86%, 2010-2023.

Justification: All companies/outcomes are included; thresholds, windows, and exclusions are robustness checks, not extra discovery tests.

Result: Hypotheses recorded before statistical stage; this is post-EDA exploratory analysis, not independent confirmation.

Limitation: Using the same dataset to form and test hypotheses limits confirmatory interpretation.

## 09 — Stage 03

Observation: Labels co-occur within documents.

Hypothesis: ML might overlap strongly with vision or knowledge processing in particular firms.

Decision: Report Jaccard and phi on all recent portfolio records, no association p-values.

Justification: Jaccard describes overlapping labels; phi describes binary association; conditioning on AI could induce associations.

Result: 140 company-component-pair estimates exported for follow-up.

Limitation: These are classifier associations, with shared text/model errors and confounding, not technological causal links.

## 10 — Stage 03

Observation: IBM 2022 count contraction has a relevant published company explanation.

Hypothesis: A selective patenting strategy could contribute to the observed contraction.

Decision: Retain the break; cite IBM Research January 2023 and inspect monthly/assignee continuity.

Justification: External primary context helps investigate an anomaly; it does not validate every captured patent or identify the effect of strategy.

Result: All main-period company-years span 12 observed months; the drop is not a missing-calendar-month artifact.

Limitation: Complete months do not prove complete counts; the source merge and entity mapping remain unaudited upstream.

## 11 — Stage 04

Observation: Annual shares show unequal patent denominators and temporal patterns.

Hypothesis: There may be systematic annual changes in classifier-defined AI/ML shares.

Decision: OLS on annual shares, unweighted years; HAC(2), n/(n-2) correction and t(12) intervals; Holm over all 10 primary tests.

Justification: A patent-level binomial test assumes independent documents/families and exaggerates precision; unweighted time units target an average annual portfolio share.

Result: Effect sizes, 95% CIs, adjusted p-values, HC3/leave-one-year-out diagnostics and alternative windows exported.

Limitation: 14 years is a small sample for HAC; model intervals do not include systematic coverage, classifier calibration or unobserved patent-family dependence.

## 12 — Stage 04

Observation: Linear trends can average acceleration or reversals.

Hypothesis: A single slope may obscure timing and company-specific portfolio shifts.

Decision: Inspect residual serial correlation and quadratic fit improvement; retain observed curves and report window sensitivity.

Justification: A linear trend is interpretable, but flexible models could overfit a short annual series; quadratic R2 is a diagnostic, not an optimized final model.

Result: Model diagnostics and residual plots saved; sensitivity p-values intentionally omitted.

Limitation: Curvature and nonstationarity weaken literal linear-trend inference, especially for hump-shaped series.

## 13 — Stage 04

Observation: IBM and NVIDIA linear ML fits extend below zero at the early endpoint.

Hypothesis: A bounded trend summary might change the direction of the descriptive pattern.

Decision: Add empirical-logit annual trend sensitivity with (count+0.5)/(n+1), retaining source flags unchanged.

Justification: This avoids taking logit(0) and produces bounded fitted shares; alternative binomial GLM would place disproportionate weight on large patent years.

Result: Odds-ratio slopes and fitted endpoint changes exported; no sensitivity significance optimization.

Limitation: The transformation changes the estimand, and it does not remove curvature, temporal dependence or classifier uncertainty.

## 14 — Stage 04

Observation: Cross-company annual differences may share common year shocks.

Hypothesis: Company trend changes may differ even after common-year dependence is considered.

Decision: Estimate all pairwise slope differences from annual difference series with HAC intervals, no secondary p-values.

Justification: Differencing incorporates contemporaneous covariance; subtracting independent standard errors would not.

Result: 20 secondary effect estimates with pointwise, explicitly exploratory intervals exported.

Limitation: Intervals are not simultaneous and cannot independently confirm data-selected contrasts.

## 15 — Stage 05

Observation: Research objective is portfolio evolution, with no independent outcome target.

Hypothesis: A predictive ML model may not improve substantive inference.

Decision: Use interpretable annual trend models only; do not train a classifier or forecast.

Justification: AI labels are threshold functions of supplied scores; fitting them would be circular. Future activity/impact outcomes are absent.

Result: No predictive ML model added; decision and reasonable extensions documented.

Limitation: Cannot assess model calibration, future grant activity, commercial relevance, or innovation quality.

## 16 — Stage 06

Observation: The original US7355601 patent lists both companies and a continuation chain to US6862027.

Hypothesis: The shared row is legitimate, and unique application IDs may still represent related patent documents.

Decision: Verify the original patent front page and text; retain all observed grants and their labels.

Justification: A document-level anomaly can be investigated with a targeted primary record instead of deleting duplicate IDs.

Result: Co-assignment is corroborated; the related Microsoft document appears under another application number. Case rows exported.

Limitation: No complete family reconstruction or human AI ground truth is supplied; broad graphics hardware may be classified as AI hardware.

## 17 — Stage 06

Observation: Deliverables must reconcile with the source and with each other.

Hypothesis: A coding or serialization error could alter conclusions despite passing the first audit.

Decision: Check all original values exactly after round-trip parsing, source hash, aggregate counts, partitions and decomposition.

Justification: These directly validate conservation and provenance; no extra modelling or significance search is needed.

Result: All checks passed; primary OLS slopes also independently matched scipy in stage 04.

Limitation: Internal consistency does not prove upstream completeness or real-world AI classification accuracy.