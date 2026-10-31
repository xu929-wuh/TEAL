# TEAL Evidence-Support Audit Subset

Version: **1.0.0**  
Release date: **2026-10-31**  
Repository: **https://github.com/xu929-wuh/TEAL**

This repository is a curated, upload-ready research subset accompanying the TEAL manuscript on trustworthy multilingual literary question answering. It contains **two 120-item human evidence-support audits**:

1. **QEA reference-answer audit** - checks whether each reference answer is supported by the QEA record's own supplied evidence.
2. **Generated-answer audit** - checks whether each system-generated answer is supported by the actual top-8 evidence presented to the question-answering system.

The repository is intentionally limited to audited research samples. It is **not** the full QEA corpus and does not redistribute complete literary works.

## Key Results

| Audit | n | Primary result |
|---|---:|---:|
| QEA reference answer, core support | 120 | **119/120 (99.17%)** |
| Generated answer, core support | 120 | **100/120 (83.33%)** |
| Generated answer, deployment subset | 40 | **39/40 (97.50%)** |

For the QEA reference-answer audit, two anonymized label sets are included. Exact three-class label agreement is **118/120 (98.33%)**, with **Cohen's kappa = 0.8673**. The annotator-A-only first-pass report is retained as `reports/qea_reference_audit_120.REPORT_ANNOTATOR_A.md` and is explicitly superseded by the paired comparison.

Supplementary strict all-claims results, which are not the primary outcome reported in the manuscript, are 111/120 for the QEA reference-answer audit, 40/120 for the generated-answer audit, and 23/40 for the deployment subset.

The generated-answer sample is deliberately stratified by language, evidence group, and output state. Its aggregate rate is **not** a natural test-set prevalence estimate. The public subset includes one final adjudicated row-level label table and the audit report; annotator-identifying information is not included.

## Repository Layout

```text
.
├─ data/
│  ├─ qea_reference_audit_120.sample.jsonl
│  ├─ qea_reference_audit_120.annotator_a.csv
│  ├─ qea_reference_audit_120.annotator_b.csv
│  ├─ qea_reference_audit_120.final_labels.csv
│  ├─ qea_reference_audit_120.adjudications.csv
│  ├─ qea_reference_audit_120.adjudications_second_pass.csv
│  ├─ generated_answer_audit_120.sample.jsonl
│  └─ generated_answer_audit_120.final_labels.csv
├─ metadata/
│  ├─ qea_reference_audit_120.sample_manifest.json
│  ├─ qea_reference_audit_120.review_comparison.json
│  ├─ generated_answer_audit_120.sample_manifest.json
│  └─ generated_answer_audit_120.report.json
├─ reports/
│  ├─ qea_reference_audit_120.REPORT_ANNOTATOR_A.md
│  ├─ qea_reference_audit_120.REPORT_ZH.md
│  ├─ qea_reference_audit_120.REVIEW_COMPARISON.md
│  ├─ generated_answer_audit_120.REPORT_EN.md
│  └─ generated_answer_audit_120.REPORT_ZH.md
├─ schemas/
│  └─ DATA_DICTIONARY.md
├─ scripts/
│  ├─ build_qea_support_audit_sample.py
│  ├─ compare_qea_support_reviews.py
│  ├─ summarize_qea_support_audit.py
│  ├─ build_generated_answer_audit_sample.py
│  ├─ summarize_generated_answer_audit.py
│  └─ verify_release.py
├─ CITATION.cff
├─ DATA_LICENSE.md
├─ LICENSE
├─ PUBLISHING_CHECKLIST.md
└─ SHA256SUMS.txt
```

## How to Inspect the Audit

The two audits contain **120 records each**. They share **35 questions**, so the package represents **205 distinct questions across 240 audit records**. Start with the summary files, then use the row-level tables and JSONL samples for detailed checks.

| Goal | Recommended file |
|---|---|
| Understand scope and headline results | `README.md` and `reports/` |
| Inspect QEA row-level labels and rationales | `data/qea_reference_audit_120.annotator_a.csv`, `data/qea_reference_audit_120.annotator_b.csv`, `data/qea_reference_audit_120.final_labels.csv` |
| Inspect QEA questions and supplied evidence | `data/qea_reference_audit_120.sample.jsonl` |
| Inspect generated-answer labels and rationales | `data/generated_answer_audit_120.final_labels.csv` |
| Inspect generated answers and the eight evidence passages | `data/generated_answer_audit_120.sample.jsonl` |
| Read machine-readable statistics | `metadata/` |
| Look up field meanings | `schemas/DATA_DICTIONARY.md` |

GitHub renders the CSV files as tables. The JSONL files contain long literary evidence passages and are not rendered as tables in the browser; download them or read them locally. `audit_id` links a sample to its annotation table. `sample_id` identifies the underlying QEA record.

To inspect one generated-answer record:

```python
import csv
import json

audit_id = "GEA-001"

with open("data/generated_answer_audit_120.sample.jsonl", encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row["audit_id"] == audit_id:
            break

with open("data/generated_answer_audit_120.final_labels.csv", encoding="utf-8-sig", newline="") as handle:
    final = next(item for item in csv.DictReader(handle) if item["audit_id"] == audit_id)

print("Question:", row["question"])
print("Generated answer:", row["generated_answer"])
print("Final label:", final["label"])
print("Reason:", final["reason"])
print("Evidence:")
for passage in row["evidence"]:
    print(f'[{passage["id"]}] {passage["text"]}')
```

For the QEA reference-answer audit, use the same `audit_id` lookup with `qea_reference_audit_120.sample.jsonl` and one of its annotation CSV files. Start with `reports/qea_reference_audit_120.REVIEW_COMPARISON.md` for the final two-annotator result.

## Reproduce Basic Checks

The included verification script uses only the Python standard library.

```bash
python scripts/verify_release.py
```

Expected checks include:

- 120 QEA audit IDs and 120 generated-answer audit IDs;
- 30 samples per language in each audit;
- QEA final labels: 111 SUPPORTED, 8 PARTIAL, 1 UNSUPPORTED;
- generated-answer labels: 40 SUPPORTED, 60 PARTIAL, 20 UNSUPPORTED;
- matching ID sets between sample files and annotation files;
- reported core support counts and the supplementary strict labels;
- sample and annotation manifests, report blocks, citation metrics, and QEA agreement statistics all match the row-level labels;
- every file listed in `SHA256SUMS.txt` exists and matches its recorded SHA256 digest.

## Audit Scope

### QEA Reference-Answer Audit

- Unit of analysis: the `evidence_text` attached to each QEA item.
- Question: does the supplied evidence support the reference answer?
- Sampling: 120 answerable QEA test items, 15 per work and 30 per language, using seed `20261025`.
- Final reporting uses the paired two-annotator comparison and adjudicated labels.

### Generated-Answer Audit

- Unit of analysis: the actual eight evidence passages presented to the question-answering system.
- Question: is the generated answer supported by those passages?
- Sampling: 120 stratified pressure samples, 30 per language, covering sufficient/insufficient/negative evidence groups and full/partial output states.
- The sample is not a natural-prevalence sample.

## Data and Privacy

- No annotator names, contact information, credentials, API keys, internal absolute paths, or user-identifying data are included.
- Work, language, sample IDs, evidence locators, and audit labels are retained for verification.
- The source-sample manifests record population counts and the sampling seed.

## Copyright and License

- Code and scripts: MIT License; see `LICENSE`.
- Project-created annotations, manifests, and reports: CC BY 4.0; see `DATA_LICENSE.md`.
- Literary excerpts remain subject to the rights of their respective source editions. The CC BY 4.0 declaration does not relicense third-party literary text.
- Full novels are not redistributed.

## Citation

Please cite the associated TEAL paper when using this audit subset. The repository is available at https://github.com/xu929-wuh/TEAL. Add the archived DOI when it is assigned.

## Publication Note

After pushing the repository:

1. confirm the citation title, version, and release date;
2. create a tagged release such as `v1.0.0`;
3. archive the release on Zenodo or an equivalent service and record the DOI;
4. add the archive DOI to `README.md`, `CITATION.cff`, the manuscript's Data and Code Availability statement, and the response to Reviewers A13 and Minor 6; the GitHub URL is already recorded here.