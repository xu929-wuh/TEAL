# QEA two-human-annotator evidence audit

- Type: two independent annotators reviewed the 120 items.
- Final rule: when the two annotators disagreed, the final reference-answer label follows the stricter judgment.
- Sample: `120` stratified answerable QEA items.
- Label agreement: `0.9833`; Cohen's kappa `0.8673`.
- Strict agreement: `0.9833`; kappa `0.8662`.
- Final strict all-claims support: `111/120 = 0.9250`; Wilson 95% CI `[0.8636, 0.9600]`.
- Final core-answer support: `119/120 = 0.9917`; Wilson 95% CI `[0.9543, 0.9985]`.
- Final labels: `{"PARTIAL": 8, "SUPPORTED": 111, "UNSUPPORTED": 1}`.

## By language

| Language | Strict support | Core support | Labels |
|---|---:|---:|---|
| en | 28/30 | 29/30 | PARTIAL=1, SUPPORTED=28, UNSUPPORTED=1 |
| fr | 30/30 | 30/30 | SUPPORTED=30 |
| ru | 26/30 | 30/30 | PARTIAL=4, SUPPORTED=26 |
| zh | 27/30 | 30/30 | PARTIAL=3, SUPPORTED=27 |

## Disagreements

- `QEA-030`: annotator A `SUPPORTED` -> annotator B `PARTIAL`; final `PARTIAL`. The evidence supports Nelly's hint and Lockwood's answer, but Nelly's alleged question about his lively look is absent from the supplied evidence.
- `QEA-078`: annotator A `SUPPORTED` -> annotator B `PARTIAL`; final `PARTIAL`. Building at Bogucharovo is supported, but the claim that Andrei spent most of his time there is not stated in the supplied evidence.

## Reporting boundary

Report core-answer support as the primary result and the final strict all-claims rate as a conservative sensitivity result. This is a two-human-annotator audit. The generated-answer audit has only one row-level label set in the current package, so its agreement statistics are not reported.
