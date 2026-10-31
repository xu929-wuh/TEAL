#!/usr/bin/env python3
"""Validate the public TEAL evidence-support audit subset."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
META = ROOT / "metadata"
LABELS = ("SUPPORTED", "PARTIAL", "UNSUPPORTED")
EXPECTED_QEA_LABELS = {"SUPPORTED": 111, "PARTIAL": 8, "UNSUPPORTED": 1}
EXPECTED_GENERATED_LABELS = {"SUPPORTED": 40, "PARTIAL": 60, "UNSUPPORTED": 20}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_true(value: object) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def normalized_labels(rows: list[dict], key: str = "label") -> dict[str, int]:
    counts = Counter(str(row[key]).strip().upper() for row in rows)
    return {label: counts[label] for label in LABELS}


def check_report_block(
    block: dict,
    rows: list[dict],
    description: str,
    errors: list[str],
) -> None:
    expected = normalized_labels(rows, "final_label")
    report_labels = {label: int(block["labels"].get(label, 0)) for label in LABELS}
    require(block["n"] == len(rows), f"{description}: n mismatch", errors)
    require(report_labels == expected, f"{description}: label counts mismatch", errors)
    require(
        block["core_answer_support"]["successes"] == sum(bool(row["final_core"]) for row in rows),
        f"{description}: core-support count mismatch",
        errors,
    )
    require(
        block["strict_all_claims"]["successes"] == expected["SUPPORTED"],
        f"{description}: strict-support count mismatch",
        errors,
    )
    citations = block["citations"]
    emitted = sum(len(row["citations"]) for row in rows)
    valid = sum(len(row["citations"]) - len(row["missing_citations"]) for row in rows)
    cited = sum(bool(row["citations"]) for row in rows)
    invalid = sum(bool(row["missing_citations"]) for row in rows)
    require(citations["emitted_mentions"] == emitted, f"{description}: citation mentions mismatch", errors)
    require(citations["valid_mentions"] == valid, f"{description}: valid citation mentions mismatch", errors)
    require(citations["rows_with_citations"] == cited, f"{description}: cited-row count mismatch", errors)
    require(citations["rows_with_invalid_citations"] == invalid, f"{description}: invalid-citation row mismatch", errors)


def is_release_file(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in {".git", "__pycache__", ".idea", ".vscode"} for part in relative.parts):
        return False
    if path.name in {".DS_Store", "Thumbs.db"} or path.name.startswith("~$"):
        return False
    return path.suffix not in {".pyc", ".log", ".tmp"}


def verify_sha256_manifest(errors: list[str]) -> int:
    manifest_path = ROOT / "SHA256SUMS.txt"
    listed: dict[str, str] = {}
    for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            errors.append(f"SHA256SUMS.txt line {line_number}: malformed entry")
            continue
        digest, relative_path = parts
        listed[relative_path] = digest
    actual_files = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != manifest_path and is_release_file(path)
    }
    require(set(listed) == actual_files, "SHA256 manifest file set does not match repository files", errors)
    for relative_path, expected in listed.items():
        path = ROOT / relative_path
        if not path.is_file():
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == expected, f"SHA256 mismatch: {relative_path}", errors)
    return len(listed)


def cohen_kappa(first: dict[str, str], second: dict[str, str], ids: set[str] | None = None) -> float:
    ids = sorted(ids if ids is not None else first)
    total = len(ids)
    observed = sum(first[key] == second[key] for key in ids) / total
    expected = sum(
        (sum(first[key] == label for key in ids) / total)
        * (sum(second[key] == label for key in ids) / total)
        for label in LABELS
    )
    return (observed - expected) / (1 - expected)


def main() -> int:
    errors: list[str] = []
    qea = load_jsonl(DATA / "qea_reference_audit_120.sample.jsonl")
    gen = load_jsonl(DATA / "generated_answer_audit_120.sample.jsonl")
    qea_a = load_csv(DATA / "qea_reference_audit_120.annotator_a.csv")
    qea_b = load_csv(DATA / "qea_reference_audit_120.annotator_b.csv")
    qea_final = load_csv(DATA / "qea_reference_audit_120.final_labels.csv")
    qea_adjudications = load_csv(DATA / "qea_reference_audit_120.adjudications.csv")
    qea_adjudications_second = load_csv(DATA / "qea_reference_audit_120.adjudications_second_pass.csv")
    gen_final = load_csv(DATA / "generated_answer_audit_120.final_labels.csv")
    qea_manifest = load_json(META / "qea_reference_audit_120.sample_manifest.json")
    gen_manifest = load_json(META / "generated_answer_audit_120.sample_manifest.json")
    gen_report = load_json(META / "generated_answer_audit_120.report.json")
    qea_comparison = load_json(META / "qea_reference_audit_120.review_comparison.json")

    require(len(qea) == 120, f"QEA sample rows: expected 120, got {len(qea)}", errors)
    require(len(gen) == 120, f"Generated sample rows: expected 120, got {len(gen)}", errors)
    require(len(qea_a) == len(qea_b) == len(qea_final) == 120,
            "QEA annotation files must each contain 120 rows", errors)
    require(len(gen_final) == 120, f"Generated labels: expected 120, got {len(gen_final)}", errors)

    qea_ids = {row["audit_id"] for row in qea}
    gen_ids = {row["audit_id"] for row in gen}
    require(len(qea_ids) == len(qea), "QEA audit IDs are not unique", errors)
    require(len(gen_ids) == len(gen), "Generated audit IDs are not unique", errors)
    require(len({row["sample_id"] for row in qea}) == len(qea), "QEA sample IDs are not unique", errors)
    require(len({row["sample_id"] for row in gen}) == len(gen), "Generated sample IDs are not unique", errors)
    require(qea_ids == {row["audit_id"] for row in qea_a}, "QEA annotator A IDs mismatch", errors)
    require(qea_ids == {row["audit_id"] for row in qea_b}, "QEA annotator B IDs mismatch", errors)
    require(qea_ids == {row["audit_id"] for row in qea_final}, "QEA final IDs mismatch", errors)
    require(gen_ids == {row["audit_id"] for row in gen_final}, "Generated final IDs mismatch", errors)

    qea_lang = Counter(row["language"] for row in qea)
    gen_lang = Counter(row["language"] for row in gen)
    require(set(qea_lang.values()) == {30}, f"QEA language imbalance: {dict(qea_lang)}", errors)
    require(set(gen_lang.values()) == {30}, f"Generated language imbalance: {dict(gen_lang)}", errors)
    require(dict(qea_lang) == qea_manifest["sample_by_language"], "QEA manifest language counts mismatch", errors)
    require(dict(Counter(row["work"] for row in qea)) == qea_manifest["sample_by_work"],
            "QEA manifest work counts mismatch", errors)
    require(qea_manifest["sample"] == len(qea), "QEA manifest sample count mismatch", errors)

    gen_strata = Counter(f"{row['language']}|{row['group']}|{row['state']}" for row in gen)
    require(gen_manifest["rows"] == len(gen), "Generated manifest row count mismatch", errors)
    require(dict(gen_lang) == gen_manifest["by_language"], "Generated manifest language counts mismatch", errors)
    require(dict(gen_strata) == gen_manifest["by_language_group_state"],
            "Generated manifest group-state counts mismatch", errors)
    require(gen_manifest["context_covers_all_gold"] == sum(bool(row["context_covers_all_gold"]) for row in gen),
            "Generated manifest context-coverage count mismatch", errors)
    require(gen_manifest["missing_citation_rows"] == sum(bool(row["missing_citations"]) for row in gen),
            "Generated manifest missing-citation count mismatch", errors)

    qea_labels = Counter(row["label"].upper() for row in qea_final)
    gen_labels = Counter(row["label"].upper() for row in gen_final)
    require(dict(qea_labels) == EXPECTED_QEA_LABELS,
            f"QEA label counts: expected {EXPECTED_QEA_LABELS}, got {dict(qea_labels)}", errors)
    require(dict(gen_labels) == EXPECTED_GENERATED_LABELS,
            f"Generated label counts: expected {EXPECTED_GENERATED_LABELS}, got {dict(gen_labels)}", errors)

    qea_core = sum(is_true(row["core_supported"]) for row in qea_final)
    qea_strict = sum(is_true(row["all_claims_supported"]) for row in qea_final)
    gen_core = sum(is_true(row["core_supported"]) for row in gen_final)
    require(qea_core == 119, f"QEA core support: expected 119, got {qea_core}", errors)
    require(qea_strict == 111, f"QEA strict support: expected 111, got {qea_strict}", errors)
    require(gen_core == 100, f"Generated core support: expected 100, got {gen_core}", errors)
    require(all((row["label"] != "UNSUPPORTED") == is_true(row["core_supported"]) for row in gen_final),
            "Generated label/core_supported values are inconsistent", errors)

    qea_a_map = {row["audit_id"]: row["label"].upper() for row in qea_a}
    qea_b_map = {row["audit_id"]: row["label"].upper() for row in qea_b}
    qea_a_map.update({row["audit_id"] + "__core": str(row["core_supported"]) for row in qea_a})
    qea_a_map.update({row["audit_id"] + "__all": str(row["all_claims_supported"]) for row in qea_a})
    qea_b_map.update({row["audit_id"] + "__core": str(row["core_supported"]) for row in qea_b})
    qea_b_map.update({row["audit_id"] + "__all": str(row["all_claims_supported"]) for row in qea_b})
    qea_final_map = {row["audit_id"]: row for row in qea_final}
    rank = {"SUPPORTED": 0, "PARTIAL": 1, "UNSUPPORTED": 2}
    for row in qea_final:
        audit_id = row["audit_id"]
        stricter_label = max(
            (qea_a_map[audit_id], qea_b_map[audit_id]),
            key=lambda label: rank[label],
        )
        require(row["label"].upper() == stricter_label,
                f"QEA final label is not the stricter judgment for {audit_id}", errors)
        strict_core = is_true(qea_a_map[audit_id + "__core"]) and is_true(qea_b_map[audit_id + "__core"])
        require(is_true(row["core_supported"]) == strict_core,
                f"QEA core support is not the conjunction for {audit_id}", errors)
        strict_all = is_true(qea_a_map[audit_id + "__all"]) and is_true(qea_b_map[audit_id + "__all"])
        require(is_true(row["all_claims_supported"]) == strict_all,
                f"QEA all-claims support is not the conjunction for {audit_id}", errors)
    for description, rows in [
        ("first-pass adjudications", qea_adjudications),
        ("second-pass adjudications", qea_adjudications_second),
    ]:
        require({row["audit_id"] for row in rows}.issubset(qea_ids),
                f"QEA {description}: unknown audit ID", errors)
        for row in rows:
            final = qea_final_map[row["audit_id"]]
            require(row["label"].upper() == final["label"].upper(),
                    f"QEA {description}: label mismatch for {row['audit_id']}", errors)
            require(is_true(row["core_supported"]) == is_true(final["core_supported"]),
                    f"QEA {description}: core mismatch for {row['audit_id']}", errors)
            require(is_true(row["all_claims_supported"]) == is_true(final["all_claims_supported"]),
                    f"QEA {description}: all-claims mismatch for {row['audit_id']}", errors)
    exact = sum(qea_a_map[key] == qea_b_map[key] for key in qea_ids)
    kappa = cohen_kappa(qea_a_map, qea_b_map, qea_ids)
    require(exact == 118, f"QEA exact label agreement: expected 118, got {exact}", errors)
    require(abs(qea_comparison["agreement"]["label_exact"] - exact / len(qea_ids)) < 1e-12,
            "QEA comparison exact-agreement value mismatch", errors)
    require(abs(qea_comparison["agreement"]["label_cohen_kappa"] - kappa) < 1e-12,
            "QEA comparison kappa value mismatch", errors)
    require(qea_comparison["final_labels"] == EXPECTED_QEA_LABELS,
            "QEA comparison final-label counts mismatch", errors)
    require(qea_comparison["final_core_answer_support"]["successes"] == qea_core,
            "QEA comparison core-support count mismatch", errors)
    require(qea_comparison["final_strict_all_claims"]["successes"] == qea_strict,
            "QEA comparison strict-support count mismatch", errors)
    for language, block in qea_comparison["by_language"].items():
        rows = [row for row in qea_final if row["language"] == language]
        report_labels = {label: int(block["labels"].get(label, 0)) for label in LABELS}
        require(report_labels == normalized_labels(rows), f"QEA comparison/{language}: label mismatch", errors)
        require(block["core_answer_support"]["successes"] == sum(is_true(row["core_supported"]) for row in rows),
                f"QEA comparison/{language}: core mismatch", errors)
        require(block["strict_all_claims"]["successes"] == sum(is_true(row["all_claims_supported"]) for row in rows),
                f"QEA comparison/{language}: strict mismatch", errors)

    gen_sample_map = {row["audit_id"]: row for row in gen}
    require(all(
        (row["group"], row["state"]) == (gen_sample_map[row["audit_id"]]["group"], gen_sample_map[row["audit_id"]]["state"])
        for row in gen_final
    ), "Generated final-label group/state metadata mismatch", errors)

    joined = []
    for sample_row in gen:
        final_row = next(row for row in gen_final if row["audit_id"] == sample_row["audit_id"])
        joined.append({
            **sample_row,
            "final_label": final_row["label"].upper(),
            "final_core": is_true(final_row["core_supported"]),
        })
    check_report_block(gen_report["overall"], joined, "Generated report/overall", errors)
    for name, block in gen_report["by_group"].items():
        check_report_block(block, [row for row in joined if row["group"] == name], f"Generated report/group/{name}", errors)
    for name, block in gen_report["by_language"].items():
        check_report_block(block, [row for row in joined if row["language"] == name], f"Generated report/language/{name}", errors)
    for name, block in gen_report["by_state"].items():
        check_report_block(block, [row for row in joined if row["state"] == name], f"Generated report/state/{name}", errors)
    for name, block in gen_report["by_group_state"].items():
        group, state = name.split("|", 1)
        rows = [row for row in joined if row["group"] == group and row["state"] == state]
        check_report_block(block, rows, f"Generated report/group-state/{name}", errors)

    deployment = [row for row in joined if row["group"] == "sufficient" and row["state"] == "full"]
    deployment_core = sum(row["final_core"] for row in deployment)
    require(len(deployment) == 40, f"Deployment subset: expected 40, got {len(deployment)}", errors)
    require(deployment_core == 39, f"Deployment core support: expected 39, got {deployment_core}", errors)
    checksum_entries = verify_sha256_manifest(errors)

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALIDATION PASSED")
    print(f"QEA reference audit: {dict(qea_labels)}; core={qea_core}/120; strict={qea_strict}/120")
    print(f"QEA agreement: exact={exact}/120; Cohen kappa={kappa:.4f}")
    print(f"Generated-answer audit: {dict(gen_labels)}; core={gen_core}/120")
    print(f"Generated report blocks: overall/group/language/group-state all match row-level labels")
    print(f"Deployment subset: core={deployment_core}/{len(deployment)}")
    print(f"Languages: QEA={dict(qea_lang)}; generated={dict(gen_lang)}")
    print(f"SHA256 manifest: {checksum_entries} entries verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
