# QEA evidence-support audit (first pass only)

> **Superseded for final reporting.** This file records annotator A's labels (113/120 strict support). The authoritative two-human-annotator result is 111/120 strict support and 119/120 core-answer support, with 118/120 three-class label agreement (Cohen's κ=0.8673); see `qea_reference_audit_120.REVIEW_COMPARISON.md` and `../metadata/qea_reference_audit_120.review_comparison.json`.

- Type: first human annotator's labels in a two-annotator evidence audit against the supplied QEA evidence. This file alone is one label set; the comparison report contains the paired human agreement statistics.
- Sample: `120` stratified answerable QEA items (15 per work; 30 per language).
- Evidence unit: the `evidence_text` attached to each QEA item, not the top-8 retrieval context.
- Scope: evidence support for the reference answer; this is not a faithfulness audit of generated answers.
- Strict all-claims support: `113/120 = 0.9417`; Wilson 95% CI `[0.8845, 0.9715]`.
- Core-answer support: `119/120 = 0.9917`; Wilson 95% CI `[0.9543, 0.9985]`.
- Labels: `{"PARTIAL": 6, "SUPPORTED": 113, "UNSUPPORTED": 1}`.

## By language

| Language | Strict support | Core support | Labels |
|---|---:|---:|---|
| en | 29/30 | 29/30 | SUPPORTED=29, UNSUPPORTED=1 |
| fr | 30/30 | 30/30 | SUPPORTED=30 |
| ru | 27/30 | 30/30 | PARTIAL=3, SUPPORTED=27 |
| zh | 27/30 | 30/30 | PARTIAL=3, SUPPORTED=27 |

## Exceptions

### QEA-018 | en | 4Wuthering Heights | UNSUPPORTED

The taunt is narrated by Nelly ("I observed aloud") and addressed to Isabella; the answer wrongly assigns the taunt to Mrs. Heathcliff.

### QEA-069 | ru | 7klmzf_brother | PARTIAL

The 100/120-ruble provision order is supported, but the extra "about 300 rubles including champagne" is absent from the supplied evidence.

### QEA-083 | ru | 8war_and_peace | PARTIAL

The proposal and refusal are supported, but "he left immediately after dinner" is absent from the supplied evidence.

### QEA-085 | ru | 8war_and_peace | PARTIAL

The quarrel and reconciliation are supported, but Ilagin's offer of hunting places is absent from the supplied evidence.

### QEA-098 | zh | 1hlm | PARTIAL

The fruit list and Zhou Rui's reply are supported, but Jia Zhen's instruction to check the account is absent from the supplied evidence.

### QEA-102 | zh | 1hlm | PARTIAL

The bribery and witness changes are supported, but the coroner's finding of a bump injury is absent from the supplied evidence.

### QEA-114 | zh | 2xiyouji | PARTIAL

The monster's fear and the plan to bind Tang in the rear garden are supported, but the named "separated-plum-blossom stratagem" and diversion of the three disciples are absent from the supplied evidence.

## Reporting boundary

The two rates answer different questions. Strict support requires every clause in the reference answer to be present in the supplied evidence. Core-answer support asks only whether the evidence contains the minimum information needed to answer the question; a PARTIAL item can still have core support while containing an unsupported secondary detail.

For a journal response, report core-answer support as the primary result and the strict all-claims rate as a conservative sensitivity result. Report inter-annotator agreement from `qea_reference_audit_120.REVIEW_COMPARISON.md`; the first-pass table alone is not the final two-annotator result.
