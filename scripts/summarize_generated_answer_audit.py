"""Merge the generated-answer audit and report support and citation metrics."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "dual_evidence_audit_v1"
LABELS = ("SUPPORTED", "PARTIAL", "UNSUPPORTED")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_annotations() -> dict[str, dict[str, Any]]:
    annotations: dict[str, dict[str, Any]] = {}
    for path in sorted(RUN.glob("annotations_v2_part_*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                audit_id = row["audit_id"].strip()
                label = row["label"].strip().upper()
                core = row["core_supported"].strip().upper() in {"YES", "TRUE", "1"}
                if label not in LABELS:
                    raise ValueError(f"bad label for {audit_id}: {label}")
                if label != "UNSUPPORTED" and not core:
                    raise ValueError(f"core inconsistency for {audit_id}: {label} but core false")
                if label == "UNSUPPORTED" and core:
                    raise ValueError(f"core inconsistency for {audit_id}: {label} but core true")
                if audit_id in annotations:
                    raise ValueError(f"duplicate annotation: {audit_id}")
                annotations[audit_id] = {**row, "label": label, "core_supported": core}
    return annotations


def wilson(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(row["label"] for row in rows)
    strict = labels["SUPPORTED"]
    core = sum(row["core_supported"] for row in rows)
    total_citations = sum(len(row["citations"]) for row in rows)
    valid_citations = sum(len(row["citations"]) - len(row["missing_citations"]) for row in rows)
    cited_rows = sum(bool(row["citations"]) for row in rows)
    invalid_rows = sum(bool(row["missing_citations"]) for row in rows)
    anchored_rows = sum(bool(row["citations"]) and not row["missing_citations"] for row in rows)
    return {
        "n": len(rows),
        "labels": {label: labels[label] for label in LABELS},
        "strict_all_claims": {"successes": strict, "total": len(rows), "rate": strict / len(rows), "wilson_95": wilson(strict, len(rows))},
        "core_answer_support": {"successes": core, "total": len(rows), "rate": core / len(rows), "wilson_95": wilson(core, len(rows))},
        "citations": {
            "rows_with_citations": cited_rows,
            "rows_with_invalid_citations": invalid_rows,
            "rows_all_emitted_citations_valid": anchored_rows,
            "emitted_mentions": total_citations,
            "valid_mentions": valid_citations,
            "micro_precision": valid_citations / total_citations if total_citations else None,
        },
    }


def by_key(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return {value: block([row for row in rows if row[key] == value]) for value in sorted({row[key] for row in rows})}


def main() -> None:
    sample = load_jsonl(RUN / "sample_120.jsonl")
    annotations = load_annotations()
    missing = [row["audit_id"] for row in sample if row["audit_id"] not in annotations]
    extra = sorted(set(annotations) - {row["audit_id"] for row in sample})
    if missing or extra:
        raise ValueError(f"annotation mismatch: missing={missing} extra={extra}")
    rows = [{**row, **annotations[row["audit_id"]]} for row in sample]
    rows.sort(key=lambda row: row["audit_id"])

    result: dict[str, Any] = {
        "audit_type": "evidence-support audit for system-generated answers; two independent annotators",
        "human_evaluation": True,
        "independent_human_iaa": None,
        "annotator_protocol": "Two independent annotators labeled the 120 system-generated answers.",
        "paired_annotation_files_available": False,
        "limitation": "The public package contains one row-level label set; the second annotator's row-level labels are not included, so generated-side agreement and Cohen kappa are not reported.",
        "sample_design": "120 stratified items; 30 per language; sufficient/insufficient/negative and full/partial deployment states deliberately oversampled; not a natural-prevalence estimate",
        "labels": {
            "SUPPORTED": "every substantive generated claim is entailed by the retrieved evidence",
            "PARTIAL": "core answer supported; at least one secondary detail is unsupported, contradicted, overstated, or a requested subpart is omitted",
            "UNSUPPORTED": "core answer unsupported, contradicted, dependent on absent evidence, or no evidence retrieved",
        },
        "overall": block(rows),
        "by_language": by_key(rows, "language"),
        "by_group": by_key(rows, "group"),
        "by_state": by_key(rows, "state"),
        "by_group_state": {
            f"{group}|{state}": block([row for row in rows if row["group"] == group and row["state"] == state])
            for group in sorted({row["group"] for row in rows})
            for state in sorted({row["state"] for row in rows if row["group"] == group})
        },
    }

    with (RUN / "annotations_120.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["audit_id", "sample_id", "language", "group", "state", "label", "core_supported", "unsupported_claims", "reason", "citations", "missing_citations"])
        for row in rows:
            writer.writerow([
                row["audit_id"], row["sample_id"], row["language"], row["group"], row["state"],
                row["label"], "YES" if row["core_supported"] else "NO",
                row["unsupported_claims"], row["reason"], ";".join(row["citations"]), ";".join(row["missing_citations"]),
            ])
    (RUN / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    overall = result["overall"]
    strict = overall["strict_all_claims"]
    core = overall["core_answer_support"]
    sf = result["by_group_state"]["sufficient|full"]
    lines = [
        "# 生成答案证据支持审计",
        "",
        "> 本审计由两位标注者分别独立完成。当前公开包只收录一套逐条标签；第二位标注者的逐条标签未收录，因此暂不报告生成侧一致率或 Cohen's κ。",
        "",
        f"- 样本：{overall['n']} 条分层样本（四语各 30 条）。抽样刻意覆盖 sufficient/insufficient/negative 与 full/partial 状态，不能当作自然流行率或总体准确率。",
        f"- 核心答案支持（主指标）：{core['successes']}/{core['total']} = {core['rate']:.2%}，Wilson 95% CI [{core['wilson_95'][0]:.2%}, {core['wilson_95'][1]:.2%}]。",
        f"- 严格全句支持（敏感性指标）：{strict['successes']}/{strict['total']} = {strict['rate']:.2%}，Wilson 95% CI [{strict['wilson_95'][0]:.2%}, {strict['wilson_95'][1]:.2%}]。",
        f"- 标签：SUPPORTED={overall['labels']['SUPPORTED']}，PARTIAL={overall['labels']['PARTIAL']}，UNSUPPORTED={overall['labels']['UNSUPPORTED']}。",
        f"- 引用：有引用答案 {overall['citations']['rows_with_citations']}/{overall['n']}；含无效引用答案 {overall['citations']['rows_with_invalid_citations']}；引用 micro precision={overall['citations']['micro_precision']:.4f}。",
        f"- 部署条件子集（sufficient+full）：核心支持 {sf['core_answer_support']['successes']}/{sf['n']} = {sf['core_answer_support']['rate']:.2%}；严格支持 {sf['strict_all_claims']['successes']}/{sf['n']} = {sf['strict_all_claims']['rate']:.2%}。",
        "",
        "## 分层结果",
        "",
        "| 维度 | 子集 | n | 核心支持 | 严格支持 | S/P/U |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for key, title in [("by_language", "语言"), ("by_group", "证据组"), ("by_state", "输出状态")]:
        for value, stats in result[key].items():
            labels = stats["labels"]
            lines.append(
                f"| {title} | {value} | {stats['n']} | {stats['core_answer_support']['successes']}/{stats['n']} ({stats['core_answer_support']['rate']:.1%}) | "
                f"{stats['strict_all_claims']['successes']}/{stats['n']} ({stats['strict_all_claims']['rate']:.1%}) | "
                f"{labels['SUPPORTED']}/{labels['PARTIAL']}/{labels['UNSUPPORTED']} |"
            )
    lines.extend(["", "### 证据组 × 输出状态", "", "| 子集 | n | 核心支持 | 严格支持 | S/P/U |", "|---|---:|---:|---:|---:|"])
    for value, stats in result["by_group_state"].items():
        labels = stats["labels"]
        lines.append(
            f"| {value} | {stats['n']} | {stats['core_answer_support']['successes']}/{stats['n']} ({stats['core_answer_support']['rate']:.1%}) | "
            f"{stats['strict_all_claims']['successes']}/{stats['n']} ({stats['strict_all_claims']['rate']:.1%}) | "
            f"{labels['SUPPORTED']}/{labels['PARTIAL']}/{labels['UNSUPPORTED']} |"
        )
    lines.extend([
        "",
        "## 口径边界",
        "",
        "- 审计判断生成答案是否由实际检索证据支持，不判断其与 QEA 参考答案字面一致。",
        "- 引用编号不存在单独记为归因缺陷，不自动改变内容支持标签。",
        "- insufficient 与 negative 是刻意纳入的压力层；总体 120 条比例不代表冻结集自然分布。",
        "- 样本按高风险状态分层，不能替代全量人工评估或推断自然测试集流行率；第二位标注者的逐条标签归档后，可补算生成侧一致率和 Cohen's κ。",
    ])
    (RUN / "REPORT_ZH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    en = [
        "# Generated-Answer Evidence-Support Audit",
        "",
        "> Two independent annotators reviewed these items. The public package contains one row-level label set; the second annotator's row-level labels are not included. Generated-side agreement and Cohen's kappa are therefore not reported.",
        "",
        f"- Sample: {overall['n']} stratified items (30 per language). The design deliberately oversamples sufficient/insufficient/negative and full/partial states; it is not a natural-prevalence or overall-accuracy estimate.",
        f"- Primary core-answer support: {core['successes']}/{core['total']} = {core['rate']:.2%}, Wilson 95% CI [{core['wilson_95'][0]:.2%}, {core['wilson_95'][1]:.2%}].",
        f"- Secondary strict all-claims support: {strict['successes']}/{strict['total']} = {strict['rate']:.2%}, Wilson 95% CI [{strict['wilson_95'][0]:.2%}, {strict['wilson_95'][1]:.2%}].",
        f"- Labels: SUPPORTED={overall['labels']['SUPPORTED']}, PARTIAL={overall['labels']['PARTIAL']}, UNSUPPORTED={overall['labels']['UNSUPPORTED']}.",
        f"- Deployment-condition subset (sufficient+full): core support {sf['core_answer_support']['successes']}/{sf['n']} = {sf['core_answer_support']['rate']:.2%}; strict support {sf['strict_all_claims']['successes']}/{sf['n']} = {sf['strict_all_claims']['rate']:.2%}.",
        f"- Citations: answers with citations {overall['citations']['rows_with_citations']}/{overall['n']}; invalid-citation answers {overall['citations']['rows_with_invalid_citations']}; micro precision {overall['citations']['micro_precision']:.4f}.",
        "",
        "The audit measures support from the retrieved context, not lexical agreement with the QEA reference answer. Invalid citation identifiers are recorded separately from content support. Because the sample deliberately oversamples high-risk states, these rates do not estimate natural test-set prevalence. The second annotator's row-level labels can be added later to calculate agreement.",
    ]
    (RUN / "REPORT_EN.md").write_text("\n".join(en) + "\n", encoding="utf-8")
    print(json.dumps({"overall": result["overall"], "sufficient_full": sf}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
