from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def parse_generation(text: str) -> tuple[str, list[str]]:
    normalized = text.replace("\r\n", "\n").strip()
    match = re.search(
        r"ANSWER:\s*(.*?)(?:\n\s*CITATIONS:\s*(.*))?$",
        normalized,
        flags=re.I | re.S,
    )
    if match:
        answer = match.group(1).strip()
        citations_text = match.group(2) or ""
    else:
        answer = normalized
        citations_text = ""
    citations = re.findall(r"E\d+", citations_text.upper())
    return answer, list(dict.fromkeys(citations))


def parse_prompt_evidence(prompt: str) -> list[dict[str, str]]:
    section = re.search(r"Candidate passages:\s*(.*?)(?:<\|im_end\|>|\Z)", prompt, re.S)
    body = section.group(1).strip() if section else ""
    matches = list(
        re.finditer(
            r"^\[E(\d+)\]\s+work=([^\n]*?)\s+chapter=([^\n]*?)\n(.*?)(?=\n\n\[E\d+\]\s+work=|\Z)",
            body,
            re.M | re.S,
        )
    )
    return [
        {
            "id": f"E{match.group(1)}",
            "work": match.group(2).strip(),
            "chapter": match.group(3).strip(),
            "text": match.group(4).strip(),
        }
        for match in matches
    ]


def sample_stratum(rows: list[dict[str, Any]], count: int, rng: random.Random) -> list[dict[str, Any]]:
    if count > len(rows):
        raise ValueError(f"requested {count} rows from a stratum with only {len(rows)}")
    by_work: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_work[row["work"]].append(row)
    pools = {work: rng.sample(sorted(rows_for_work, key=lambda row: row["sample_id"]), len(rows_for_work))
             for work, rows_for_work in by_work.items()}
    selected: list[dict[str, Any]] = []
    works = sorted(pools)
    while len(selected) < count:
        progressed = False
        for work in works:
            if len(selected) >= count:
                break
            if pools[work]:
                selected.append(pools[work].pop())
                progressed = True
        if not progressed:
            raise ValueError("work-level pools exhausted before reaching requested count")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--graded",
        type=Path,
        default=Path("paper/1english/revision_2026/method_v2/runs/graded_answer_policy_v2/frozen587_graded.jsonl"),
    )
    parser.add_argument(
        "--contexts",
        type=Path,
        default=Path("paper/1english/revision_2026/method_v2/runs/test_frozen_v14/contexts_test_eni_reader800_top8.jsonl"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("paper/1english/revision_2026/method_v2/runs/dual_evidence_audit_v1"),
    )
    parser.add_argument("--seed", type=int, default=20261025)
    args = parser.parse_args()

    graded = load_jsonl(args.graded)
    contexts = {row["sample_id"]: row for row in load_jsonl(args.contexts)}
    if not all(row["sample_id"] in contexts for row in graded):
        raise ValueError("graded rows do not all have a matching context row")
    for row in graded:
        row["work"] = contexts[row["sample_id"]].get("work", "")

    quotas: dict[str, list[tuple[str, str | None, int]]] = {
        "en": [
            ("sufficient", "full", 10),
            ("sufficient", "partial", 5),
            ("insufficient", "full", 8),
            ("insufficient", "partial", 6),
            ("negative", None, 1),
        ],
        "fr": [
            ("sufficient", "full", 10),
            ("sufficient", "partial", 5),
            ("insufficient", "full", 8),
            ("insufficient", "partial", 6),
            ("negative", None, 1),
        ],
        "ru": [
            ("sufficient", "full", 10),
            ("sufficient", "partial", 5),
            ("insufficient", "full", 8),
            ("insufficient", "partial", 6),
            ("negative", None, 1),
        ],
        "zh": [
            ("sufficient", "full", 10),
            ("sufficient", "partial", 5),
            ("insufficient", "full", 6),
            ("insufficient", "partial", 7),
            ("negative", None, 2),
        ],
    }

    rng = random.Random(args.seed)
    selected: list[dict[str, Any]] = []
    for language in sorted(quotas):
        for group, state, count in quotas[language]:
            pool = [
                row
                for row in graded
                if row["language"] == language
                and row["group"] == group
                and row["state"] in ({"full", "partial"} if state is None else {state})
            ]
            selected.extend(sample_stratum(pool, count, rng))

    selected.sort(key=lambda row: (row["language"], row["group"], row["state"], row["sample_id"]))
    for index, row in enumerate(selected, start=1):
        context = contexts[row["sample_id"]]
        answer, citations = parse_generation(row["final_text"])
        evidence = parse_prompt_evidence(context.get("prompt", ""))
        evidence_ids = {item["id"] for item in evidence}
        missing_citations = [citation for citation in citations if citation not in evidence_ids]
        row_out = {
            "audit_id": f"GEA-{index:03d}",
            "sample_id": row["sample_id"],
            "language": row["language"],
            "work": context.get("work", ""),
            "group": row["group"],
            "state": row["state"],
            "question": row["question"],
            "generated_answer": answer,
            "citations": citations,
            "missing_citations": missing_citations,
            "evidence": evidence,
            "gold_answer": row["gold_answer"],
            "gate_score": row["gate_score"],
            "verifier_score": row["verifier_score"],
            "context_covers_all_gold": context.get("context_covers_all_gold"),
        }
        selected[index - 1] = row_out

    if len(selected) != 120:
        raise AssertionError(f"expected 120 sampled rows, got {len(selected)}")
    if len({row["sample_id"] for row in selected}) != 120:
        raise AssertionError("sampled rows are not unique")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    sample_path = args.out_dir / "sample_120.jsonl"
    with sample_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "rows": len(selected),
        "seed": args.seed,
        "by_language": dict(sorted(Counter(row["language"] for row in selected).items())),
        "by_language_group_state": {
            f"{language}|{group}|{state}": count
            for (language, group, state), count in sorted(
                Counter(
                    (row["language"], row["group"], row["state"]) for row in selected
                ).items()
            )
        },
        "missing_citation_rows": sum(bool(row["missing_citations"]) for row in selected),
        "context_covers_all_gold": sum(bool(row["context_covers_all_gold"]) for row in selected),
    }
    (args.out_dir / "sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    print(sample_path)


if __name__ == "__main__":
    main()
