# AI Patent Analysis

A reproducible analysis of AI-related U.S. patents assigned to **IBM, NVIDIA, Qualcomm, Google, and Microsoft**.

The project has two parts:

1. **`analysis/`** — validation, cleaning, exploratory analysis, trend analysis, sensitivity checks, and the decision not to force a circular predictive model.
2. **`cpc_extension/`** — CPC/text enrichment focused on two questions raised by the first analysis:
   - Why did Qualcomm's classifier-negative patent denominator expand?
   - What technologies account for NVIDIA's shift toward ML-labelled patents?

## Main findings

- NVIDIA shows a large shift toward ML-labelled patents, supported by CPC and explicit learning/neural-network text rather than classifier flags alone.
- IBM's absolute AI-labelled patent volume falls in recent years while AI concentration within the captured portfolio rises.
- Qualcomm's AI-labelled patent count rises, but its AI share falls because total captured patent volume expands faster.
- The CPC/text extension finds that Qualcomm's 2021–2023 classifier-negative expansion is overwhelmingly concentrated in communications patents, especially wireless-networking activity.
- The extension also finds that NVIDIA's ML shift is strongly associated with explicit learned-method text, vision/image technologies, autonomous-system perception, and selected accelerator inventions.

These are descriptive findings about the supplied patent extract. Classifier scores are model outputs, not verified ground truth, and the captured assignee records should not be interpreted automatically as complete corporate patent portfolios.

## Repository structure

```text
AI_Patent/
├── analysis/             # Main five-company analysis
├── cpc_extension/        # CPC/text follow-up analysis
├── data/README.md        # Local input/data notes and checksums
└── .gitignore
```

Start with:

- `analysis/outputs/analysis_report.md`
- `cpc_extension/outputs/technology_report.md`

Each section contains its own README, requirements, executable Python pipeline, audit/verification outputs, and selected result tables.

## Data

Large/raw data are intentionally not committed directly to Git. See `data/README.md` for expected filenames, sizes, SHA-256 hashes, and reproduction notes.

The main analysis expects the locally supplied source file:

```text
five_big_tech_ai_patents.csv
```

The CPC/text extension contains code to reproduce enrichment from fixed-release USPTO PatentsView data and can refresh the government subsets with its documented pipeline.

## Reproducibility

The analysis is deterministic: there is no random sampling and no fitted predictive model. The project keeps explicit validation and verification stages and records important research decisions and limitations.

Python 3.12 was used for the reference runs. Install the requirements within the relevant project directory before running a pipeline.

## Interpretation cautions

- AI/ML thresholds are operational classifier definitions, not truth labels.
- Patent documents are not necessarily independent inventions because continuations, reissues, and related family members can appear separately.
- Assignee matching does not by itself prove complete corporate portfolio coverage.
- Counts and shares answer different questions and should be interpreted together.
- Statistical trend tests in the main analysis are exploratory rather than confirmatory.
