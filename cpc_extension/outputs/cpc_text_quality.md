# CPC/text field quality and provenance

This document records provenance and limitations of the CPC, title, abstract and filing-date fields added for the technology analysis.

All six bulk ZIP files match the release's published MD5 and byte counts. Title, abstract and direct filing-date fields are nonempty for all 7,813 selected grants. Current CPC is present for 7,807; the six exceptions are genuine reissues and are retained. At-issue CPC is unavailable for 267 early NVIDIA grants, so its comparative sensitivity uses paired records rather than treating absence as a technology zero.

| doc_id | company | cohort | patent_title | is_reissue |
| --- | --- | --- | --- | --- |
| RE48709 | Qualcomm | 2021 | Method and apparatus for reporting a channel quality in a wireless communication system | 1 |
| RE49591 | Qualcomm | 2023 | Power saving techniques in computing devices | 1 |
| RE49652 | Qualcomm | 2023 | Power saving techniques in computing devices | 1 |
| RE45757 | NVIDIA | 2014-2016 | Cellular wireless internet access system using spread spectrum and internet protocol | 1 |
| RE48876 | NVIDIA | 2021-2023 | Near-eye parallax barrier displays | 1 |
| RE49711 | NVIDIA | 2021-2023 | Distributed digital low-dropout voltage micro regulator | 1 |

No negative, unparseable or greater-than-30-year grant lags occur in the Qualcomm negative-grant timing cohort. Source rows, raw CPC records and original classifier values remain available. Missing current CPC is not filled with inferred codes, and text/classifier disagreements are not relabeled.