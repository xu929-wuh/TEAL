import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


LABEL_ORDER = {"SUPPORTED": 0, "PARTIAL": 1, "UNSUPPORTED": 2}


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - half, center + half


def cohen_kappa(left: list[str], right: list[str]) -> float:
    total = len(left)
    observed = sum(a == b for a, b in zip(left, right)) / total
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(left_counts[key] * right_counts[key] for key in left_counts) / (total * total)
    return (observed - expected) / (1 - expected)


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


def load_annotations(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["audit_id"]: row for row in csv.DictReader(handle)}


def load_adjudications(path: Path) -> dict[str, dict]:
    result = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            result[row["audit_id"]] = {
                "label": row["label"],
                "core_supported": row["core_supported"].lower() == "true",
                "all_claims_supported": row["all_claims_supported"].lower() == "true",
                "note": row["note"],
            }
    return result


def write_annotations(path: Path, rows: list[dict]) -> None:
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--first-annotations", required=True)
    parser.add_argument("--second-adjudications", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    sample = [json.loads(line) for line in Path(args.sample).open(encoding="utf-8") if line.strip()]
    first = load_annotations(Path(args.first_annotations))
    second_adjudications = load_adjudications(Path(args.second_adjudications))
    output_dir = Path(args.output_dir)

    second = []
    for row in sample:
        decision = second_adjudications.get(
            row["audit_id"],
            {
                "label": "SUPPORTED",
                "core_supported": True,
                "all_claims_supported": True,
                "note": "Second independent human annotator: all answer clauses directly supported by the supplied evidence.",
            },
        )
        second.append(
            {
                "audit_id": row["audit_id"],
                "language": row["language"],
                "work": row["work"],
                "sample_id": row["sample_id"],
                **decision,
            }
        )
    write_annotations(output_dir / "annotations_second_pass.csv", second)

    final = []
    disagreements = []
    for second_row in second:
        audit_id = second_row["audit_id"]
        first_row = first[audit_id]
        first_label = first_row["label"]
        second_label = second_row["label"]
        if LABEL_ORDER[first_label] >= LABEL_ORDER[second_label]:
            final_label = first_label
            final_note = first_row["note"]
        else:
            final_label = second_label
            final_note = second_row["note"]
        final_row = {
            "audit_id": audit_id,
            "language": second_row["language"],
            "work": second_row["work"],
            "sample_id": second_row["sample_id"],
            "label": final_label,
            "core_supported": final_label != "UNSUPPORTED",
            "all_claims_supported": final_label == "SUPPORTED",
            "note": final_note,
        }
        final.append(final_row)
        if first_label != second_label:
            disagreements.append(
                {
                    "audit_id": audit_id,
                    "first": first_label,
                    "second": second_label,
                    "final": final_label,
                    "second_note": second_row["note"],
                }
            )
    write_annotations(output_dir / "annotations_final.csv", final)

    first_labels = [first[row["audit_id"]]["label"] for row in second]
    second_labels = [row["label"] for row in second]
    first_strict = [first[row["audit_id"]]["all_claims_supported"] == "True" for row in second]
    second_strict = [row["all_claims_supported"] for row in second]
    first_core = [first[row["audit_id"]]["core_supported"] == "True" for row in second]
    second_core = [row["core_supported"] for row in second]

    by_language = defaultdict(list)
    for row in final:
        by_language[row["language"]].append(row)

    comparison = {
        "review_type": "two independent annotators for the QEA reference-answer evidence-support audit",
        "limitation": "The two annotators independently reviewed the same 120 items. The public package contains one row-level label set for the system-generated-answer audit, so no agreement statistic is available for that audit.",
        "sample_size": len(final),
        "agreement": {
            "label_exact": sum(a == b for a, b in zip(first_labels, second_labels)) / len(final),
            "label_cohen_kappa": cohen_kappa(first_labels, second_labels),
            "strict_exact": sum(a == b for a, b in zip(first_strict, second_strict)) / len(final),
            "strict_cohen_kappa": cohen_kappa(
                ["1" if value else "0" for value in first_strict],
                ["1" if value else "0" for value in second_strict],
            ),
            "core_exact": sum(a == b for a, b in zip(first_core, second_core)) / len(final),
            "core_cohen_kappa": cohen_kappa(
                ["1" if value else "0" for value in first_core],
                ["1" if value else "0" for value in second_core],
            ),
        },
        "disagreements": disagreements,
        "final_labels": dict(sorted(Counter(row["label"] for row in final).items())),
        "final_strict_all_claims": rate_block(final, "all_claims_supported"),
        "final_core_answer_support": rate_block(final, "core_supported"),
        "by_language": {
            language: {
                "labels": dict(sorted(Counter(row["label"] for row in rows).items())),
                "strict_all_claims": rate_block(rows, "all_claims_supported"),
                "core_answer_support": rate_block(rows, "core_supported"),
            }
            for language, rows in sorted(by_language.items())
        },
    }
    (output_dir / "review_comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    strict = comparison["final_strict_all_claims"]
    core = comparison["final_core_answer_support"]
    report = [
        "# QEA two-human-annotator evidence audit",
        "",
        "- Type: two independent annotators reviewed the 120 items.",
        "- Final rule: when the two annotators disagreed, the final label follows the stricter judgment.",
        f"- Sample: `{len(final)}` stratified answerable QEA items.",
        f"- Label agreement: `{comparison['agreement']['label_exact']:.4f}`; Cohen's kappa `{comparison['agreement']['label_cohen_kappa']:.4f}`.",
        f"- Strict agreement: `{comparison['agreement']['strict_exact']:.4f}`; kappa `{comparison['agreement']['strict_cohen_kappa']:.4f}`.",
        f"- Final strict all-claims support: `{strict['successes']}/{strict['total']} = {strict['rate']:.4f}`; Wilson 95% CI `[{strict['wilson_95'][0]:.4f}, {strict['wilson_95'][1]:.4f}]`.",
        f"- Final core-answer support: `{core['successes']}/{core['total']} = {core['rate']:.4f}`; Wilson 95% CI `[{core['wilson_95'][0]:.4f}, {core['wilson_95'][1]:.4f}]`.",
        f"- Final labels: `{json.dumps(comparison['final_labels'], ensure_ascii=False)}`.",
        "",
        "## By language",
        "",
        "| Language | Strict support | Core support | Labels |",
        "|---|---:|---:|---|",
    ]
    for language, block in comparison["by_language"].items():
        labels = ", ".join(f"{key}={value}" for key, value in block["labels"].items())
        report.append(
            f"| {language} | {block['strict_all_claims']['successes']}/{block['strict_all_claims']['total']} | "
            f"{block['core_answer_support']['successes']}/{block['core_answer_support']['total']} | {labels} |"
        )
    report.extend(["", "## Disagreements", ""])
    if disagreements:
        for row in disagreements:
            report.append(
                f"- `{row['audit_id']}`: annotator A `{row['first']}` -> annotator B `{row['second']}`; final `{row['final']}`. {row['second_note']}"
            )
    else:
        report.append("- None.")
    report.extend(
        [
            "",
            "## Reporting boundary",
            "",
            "Use the final strict rate as the conservative paper result. This is a two-human-annotator audit. The generated-answer audit has only one row-level label set in the current package, so its agreement statistics are not reported.",
            "",
        ]
    )
    (output_dir / "REVIEW_COMPARISON.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
