# Data-quality report: five-company patent extract

Audit outcome: no hard internal integrity failures. The source contains 271,415 rows, 46 columns and 271,414 distinct granted patent documents. No rows are excluded from the derived master dataset. This is a conditional pass for internal structure; source-level merge recall and corporate-group coverage cannot be established.

| Check | Result |
| --- | --- |
| Document/patent key equality | 0 mismatches |
| Identifier syntax | All IDs valid; 143 valid RE reissues |
| Application identifiers | All 8-character strings; leading zeros preserved |
| Exact duplicate rows | 0 |
| Duplicate patent-company memberships | 0 |
| Shared patent | 7355601, IBM and Microsoft; document metadata identical |
| AI classification rules | All 24 component/cutoff checks pass; all 3 any-AI OR checks pass |
| Score range / nested flags | All scores within [0,1]; all flags binary and nested |
| Missing values | Only location_id: 230 rows (0.0847%); no imputation |
| Publication dates | 1976-01-06 through 2023-12-26; all Tuesday grants |
| Comparable window | 2010-2023: 14 years per company, >=156 grants/year, all 12 months observed |
| Unmatched source records | Not observable; no upstream tables or merge manifest supplied |
| Assignee coverage | 10 observed IDs; Google has 1, the other firms have 2 or 3 |

## Observed company coverage

| company | rows | unique_patents | first_date | last_date | assignee_ids | missing_location |
| --- | --- | --- | --- | --- | --- | --- |
| Google | 25520 | 25520 | 2003-02-25 | 2023-12-26 | 1 | 60 |
| IBM | 159001 | 159001 | 1976-01-06 | 2023-12-26 | 2 | 55 |
| Microsoft | 47352 | 47352 | 1986-05-13 | 2023-12-26 | 2 | 45 |
| NVIDIA | 4491 | 4491 | 1997-04-08 | 2023-12-26 | 2 | 9 |
| Qualcomm | 35051 | 35051 | 1989-10-24 | 2023-12-26 | 3 | 61 |

Assignee names are disambiguated entity names. Google has one supplied GOOGLE LLC ID, and Microsoft has two major IDs with a historical name/entity transition. These facts do not prove omissions, and names alone cannot establish full subsidiary, acquired-portfolio or current-ownership coverage. The supplied denominators are captured patent portfolios, not certified corporate totals.

The supplied predict93 fields agree with score >=0.93. Therefore the older 89.93% threshold problem described in USPTO release notes is not present in these flags. This verifies the cutoff behavior, not the file release provenance.

Targeted external check: the original US7355601 front page confirms the IBM/Microsoft assignees and 2008 issue date. Its continuation chain identifies US6862027, also captured here under Microsoft with a different application ID. Family dependence is therefore a concrete feature, not only a hypothetical concern.

## Transformations and exclusions

| analysis | reason | rows_excluded | rows_retained |
| --- | --- | --- | --- |
| clean dataset and full-history EDA | none | 0 | 271415 |
| main annual trends and equal-year comparison | outside calendar grant years 2010-2023 | 73599 | 197816 |
| recent technology profile and co-occurrence | outside grant years 2021-2023 | 234310 | 37105 |
| no-reissue sensitivity only | valid RE patents omitted as a sensitivity | 143 | 271272 |
| pooled unique document summary only | collapse co-assignee memberships to a single consistent document, retain both in main dataset | 1 | 271414 |
| small observed entity sensitivity only | omit assignee IDs comprising less than 1% of their company records in this extract | 673 | 270742 |

Every original column and row is retained in clean_patent_company.csv.gz. IDs remain strings; dates supply calendar features; overlapping component counts, hardware-only/nonhardware indicators, within-sample membership weights and analysis eligibility flags are added. Missing locations and reissues are retained. Each sensitivity restriction is confined to that analysis and recorded in the scope ledger. source_row_number maps derived rows back to the original CSV line.

## Verification and unresolved checks

- All source values survive exact dataframe round-trip comparison; the original file SHA-256 remains unchanged.
- Annual totals, all AI thresholds, component partitions, fractional membership sums and count-change decomposition reconcile.
- Still needed for a source merge audit: original assignee and AIPD tables, versions, company mapping, left/anti-join counts, and unmatched ID examples.
- Still needed for family counting: reissue parents, continuation relationships and patent-family IDs; these are absent.
- Still needed for substantive validation: patent text/claims and a stratified, independently reviewed label sample.

Original CSV SHA-256: d34cf61d30554b30ddb6d8e7f06f7a3bc130799f643f95aef6c282d53de69e79

- [USPTO dataset and release notes](https://www.uspto.gov/ip-policy/economic-research/research-datasets/artificial-intelligence-patent-dataset)
- [USPTO AIPD 2023 methodology, especially appendices D–E](https://www.uspto.gov/sites/default/files/documents/oce-aipd-2023.pdf)
- [IBM Research, How do you measure innovation?, 9 January 2023](https://research.ibm.com/blog/Ibm-innovation-2022)
- [Original patent US7355601, front page and continuation/text disclosures](https://patentimages.storage.googleapis.com/0b/8e/3c/ca176069e305fb/US7355601.pdf)