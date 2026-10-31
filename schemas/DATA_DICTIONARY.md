# Data Dictionary

## Work Codes

| Code | Work |
|---|---|
| `1hlm` | 红楼梦 / Dream of the Red Chamber |
| `2xiyouji` | 西游记 / Journey to the West |
| `3pride_prejudice` | Pride and Prejudice |
| `4Wuthering Heights` | Wuthering Heights |
| `5bc_world` | 悲惨世界 / Les Miserables |
| `6red_and_black` | 红与黑 / Le Rouge et le Noir |
| `7klmzf_brother` | 卡拉马佐夫兄弟 / The Brothers Karamazov |
| `8war_and_peace` | 战争与和平 / War and Peace |

## Language Codes

- `en`: English
- `fr`: French
- `ru`: Russian
- `zh`: Chinese

## QEA Reference-Answer Sample

File: `data/qea_reference_audit_120.sample.jsonl`

One JSON object per line. Important fields:

| Field | Meaning |
|---|---|
| `audit_id` | Audit identifier `QEA-001` to `QEA-120`. |
| `sample_id` | QEA record identifier. |
| `question` | Question used for the QEA item. |
| `gold_answer` | Reference answer. |
| `evidence_text` | Evidence text supplied with the QEA record. |
| `gold_evidence` | Evidence passages supporting the reference answer. |
| `language` | Language code. |
| `work` | Work code. |
| `group_id` | Leakage-control question-group identifier. |
| `source_file`, `source_line`, `source_lines` | Source locator metadata. |
| `release_version` | Record-level provenance stamp carried by the source record; the sampling source is the `dataset_release_v14` test file identified in the sample manifest. |
| `label` | Source answerability flag (`answerable`), not the evidence-support audit label. |
| `split`, `source_split` | Evaluation split metadata. |

The sample file may include additional provenance and quality-control fields from the original release. Evidence-support labels are reported only in the companion CSV files.

## QEA Annotation Files

Files:

- `data/qea_reference_audit_120.annotator_a.csv`
- `data/qea_reference_audit_120.annotator_b.csv`
- `data/qea_reference_audit_120.final_labels.csv`

Fields:

| Field | Meaning |
|---|---|
| `audit_id` | Audit identifier. |
| `language` | Language code. |
| `work` | Work code. |
| `sample_id` | QEA sample identifier. |
| `label` | `SUPPORTED`, `PARTIAL`, or `UNSUPPORTED`. |
| `core_supported` | Whether the minimum information needed to answer is supported. |
| `all_claims_supported` | Whether every answer claim is supported. |
| `note` | Short audit rationale. |

## QEA Adjudication Files

Files:

- `data/qea_reference_audit_120.adjudications.csv`
- `data/qea_reference_audit_120.adjudications_second_pass.csv`

These files list disagreements and resolution notes. They supplement, but do not replace, the final label table.

## Generated-Answer Sample

File: `data/generated_answer_audit_120.sample.jsonl`

Important fields:

| Field | Meaning |
|---|---|
| `audit_id` | Audit identifier `GEA-001` to `GEA-120`. |
| `sample_id` | QEA sample identifier. |
| `question` | Question presented to the system. |
| `gold_answer` | Reference answer. |
| `generated_answer` | Raw system-generated answer. |
| `evidence` | Actual top-8 evidence passages presented to the question-answering system. |
| `citations` | Citation labels used by the generated answer. |
| `group` | `sufficient`, `insufficient`, or `negative`. |
| `state` | `full` or `partial` output state. |
| `context_covers_all_gold` | Whether retrieved context covers all gold evidence. |
| `gate_score`, `verifier_score` | Decision scores. |
| `language`, `work` | Language and work codes. |
| `missing_citations` | Missing-citation audit field. |

## Generated-Answer Annotation File

File: `data/generated_answer_audit_120.final_labels.csv`

Fields:

| Field | Meaning |
|---|---|
| `audit_id` | Audit identifier. |
| `sample_id` | QEA sample identifier. |
| `language`, `work` | Language and work codes. |
| `group` | Evidence group. |
| `state` | Output state. |
| `label` | `SUPPORTED`, `PARTIAL`, or `UNSUPPORTED`. |
| `core_supported` | `YES`/`NO` for core-answer support. |
| `unsupported_claims` | Summary of unsupported claims. |
| `reason` | Audit rationale. |
| `citations` | Citations present in the answer. |
| `missing_citations` | Missing citations, if any. |

## Label Semantics

- `SUPPORTED`: all material claims are supported by the supplied evidence.
- `PARTIAL`: the core answer is supported, but at least one secondary claim is unsupported or missing.
- `UNSUPPORTED`: the core answer is not supported by the supplied evidence.

For QEA reference answers, `core_supported` is the primary metric and `all_claims_supported` is the conservative strict metric. For generated answers, the same distinction is used.