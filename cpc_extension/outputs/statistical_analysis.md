# Statistical analysis — finite-cohort composition accounting

All analyses are exploratory. The estimands are descriptive counts, proportions and net-count attributions for the selected source rows, not population or causal effects. No significance tests or fitted prediction models are necessary for these exact accounting questions.

| company | share_change_pp | positive_count_contribution_pp | negative_count_contribution_pp |
| --- | --- | --- | --- |
| Qualcomm | -3.855 | +3.258 | -7.113 |
| NVIDIA | +28.569 | +22.990 | +5.579 |

Let s(P,N)=P/(P+N). The positive-count contribution is one-half of [s(P1,N0)−s(P0,N0)] plus [s(P1,N1)−s(P0,N1)]; the negative-count contribution averages the two corresponding negative-count updates. Their sum equals the observed share change. This is Shapley accounting, not a causal model.

| company | feature | full_change_pp | leave_one_quarter_min_pp | leave_one_quarter_max_pp |
| --- | --- | --- | --- | --- |
| Qualcomm | text_combined_sidelink | 10.293 | 9.677 | 10.666 |
| NVIDIA | text_combined_explicit_learning_or_neural | 23.791 | 23.109 | 24.451 |

No sampling confidence interval applies to the known count of these supplied grants. A confidence interval for a repeatable patent-generation process would require an explicit sampling/process model, independent or adequately clustered families, and enough temporal units. Those conditions are not established. The sensitivity ranges above do not have 95% coverage and are not labeled confidence intervals. Initial-analysis statistical results are separate; no new confirmatory test is claimed here.