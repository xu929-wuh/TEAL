import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - half, center + half


def rate_block(rows: list[dict], key: str) -> dict:
    total = len(rows)
    successes = sum(bool(row[key]) for row in rows)
    low, high = wilson_interval(successes, total)
    return {
        "successes": successes,
        "total": total,
        "rate": successes / total if total else 0.0,
        "wilson_95": [low, high],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--adjudications", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    sample_path = Path(args.sample)
    output_dir = Path(args.output_dir)
    sample = [json.loads(line) for line in sample_path.open(encoding="utf-8") if line.strip()]
    sample_by_id = {row["audit_id"]: row for row in sample}

    adjudications = {}
    with Path(args.adjudications).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            adjudications[row["audit_id"]] = {
                "label": row["label"],
                "core_supported": row["core_supported"].lower() == "true",
                "all_claims_supported": row["all_claims_supported"].lower() == "true",
                "note": row["note"],
            }

    unknown = sorted(set(adjudications) - set(sample_by_id))
    if unknown:
        raise ValueError(f"Adjudications outside sample: {unknown}")

    annotations = []
    for row in sample:
        decision = adjudications.get(
            row["audit_id"],
            {
                "label": "SUPPORTED",
                "core_supported": True,
                "all_claims_supported": True,
                "note": "All answer clauses directly supported by the supplied evidence.",
            },
        )
        annotations.append(
            {
                "audit_id": row["audit_id"],
                "language": row["language"],
                "work": row["work"],
                "sample_id": row["sample_id"],
                **decision,
            }
        )

    columns = [
        "audit_id",
        "language",
        "work",
        "sample_id",
        "label",
        "core_supported",
        "all_claims_supported",
        "note",
    ]
    with (output_dir / "annotations.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(annotations)

    by_language = defaultdict(list)
    by_work = defaultdict(list)
    for row in annotations:
        by_language[row["language"]].append(row)
        by_work[row["work"]].append(row)

    summary = {
    "audit_type": "first human annotator label set for the QEA evidence-support audit",
        "limitation": "This file contains only the first annotator labels; use the paired comparison report for inter-annotator agreement and final results.",
        "sample_size": len(annotations),
        "labels": dict(sorted(Counter(row["label"] for row in annotations).items())),
        "strict_all_claims": rate_block(annotations, "all_claims_supported"),
        "core_answer_support": rate_block(annotations, "core_supported"),
        "by_language": {
            language: {
                "labels": dict(sorted(Counter(row["label"] for row in rows).items())),
                "strict_all_claims": rate_block(rows, "all_claims_supported"),
                "core_answer_support": rate_block(rows, "core_supported"),
            }
            for language, rows in sorted(by_language.items())
        },
        "by_work": {
            work: {
                "labels": dict(sorted(Counter(row["label"] for row in rows).items())),
                "strict_all_claims": rate_block(rows, "all_claims_supported"),
                "core_answer_support": rate_block(rows, "core_supported"),
            }
            for work, rows in sorted(by_work.items())
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    strict = summary["strict_all_claims"]
    core = summary["core_answer_support"]
    report = [
        "# QEA evidence-support audit",
        "",
        "- Type: first human annotator's labels in the two-annotator audit against the supplied QEA evidence.",
        "- This first-pass file alone is not the final paired result; see the two-annotator comparison report.",
        f"- Sample: `{len(annotations)}` stratified answerable QEA items (15 per work; 30 per language).",
        "- Evidence unit: the `evidence_text` attached to each QEA item, not the top-8 retrieval context.",
        "- Scope: evidence support for the reference answer; this is not a faithfulness audit of generated answers.",
        f"- Strict all-claims support: `{strict['successes']}/{strict['total']} = {strict['rate']:.4f}`; Wilson 95% CI `[{strict['wilson_95'][0]:.4f}, {strict['wilson_95'][1]:.4f}]`.",
        f"- Core-answer support: `{core['successes']}/{core['total']} = {core['rate']:.4f}`; Wilson 95% CI `[{core['wilson_95'][0]:.4f}, {core['wilson_95'][1]:.4f}]`.",
        f"- Labels: `{json.dumps(summary['labels'], ensure_ascii=False)}`.",
        "",
        "## By language",
        "",
        "| Language | Strict support | Core support | Labels |",
        "|---|---:|---:|---|",
    ]
    for language, block in summary["by_language"].items():
        labels = ", ".join(f"{key}={value}" for key, value in block["labels"].items())
        report.append(
            f"| {language} | {block['strict_all_claims']['successes']}/{block['strict_all_claims']['total']} | "
            f"{block['core_answer_support']['successes']}/{block['core_answer_support']['total']} | {labels} |"
        )
    report.extend(
        [
            "",
            "## Exceptions",
            "",
        ]
    )
    for row in annotations:
        if row["label"] != "SUPPORTED":
            report.extend(
                [
                    f"### {row['audit_id']} | {row['language']} | {row['work']} | {row['label']}",
                    "",
                    row["note"],
                    "",
                ]
            )
    report.extend(
        [
            "## Reporting boundary",
            "",
            "The two rates answer different questions. Strict support requires every clause in the reference answer to be present in the supplied evidence. Core-answer support asks only whether the evidence contains the minimum information needed to answer the question; a PARTIAL item can still have core support while containing an unsupported secondary detail.",
            "",
            "For a journal response, the conservative number is the strict all-claims rate. Do not call this table a human evaluation without an independent second annotator.",
            "",
        ]
    )
    (output_dir / "REPORT_ANNOTATOR_A.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
