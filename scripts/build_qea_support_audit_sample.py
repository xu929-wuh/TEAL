import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--per-work", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()

    source = Path(args.source)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(line) for line in source.open(encoding="utf-8") if line.strip()]
    by_work = {}
    for row in rows:
        by_work.setdefault(row["work"], []).append(row)

    rng = random.Random(args.seed)
    sampled = []
    for work in sorted(by_work):
        candidates = sorted(by_work[work], key=lambda row: row["sample_id"])
        if len(candidates) < args.per_work:
            raise ValueError(f"{work} has only {len(candidates)} rows")
        sampled.extend(rng.sample(candidates, args.per_work))

    sampled.sort(key=lambda row: (row["language"], row["work"], row["sample_id"]))
    for index, row in enumerate(sampled, start=1):
        row["audit_id"] = f"QEA-{index:03d}"

    sample_path = output_dir / "sample_120.jsonl"
    with sample_path.open("w", encoding="utf-8") as handle:
        for row in sampled:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    review_lines = [
        "# QEA evidence-support audit sample",
        "",
        f"- source: `{source.as_posix()}`",
        f"- source_sha256: `{sha256(source)}`",
        f"- seed: `{args.seed}`",
        f"- population: `{len(rows)}`",
        f"- sample: `{len(sampled)}`",
        f"- per_work: `{args.per_work}`",
        "- labels: SUPPORTED / PARTIAL / UNSUPPORTED / EVIDENCE_BUG",
        "",
    ]
    for row in sampled:
        review_lines.extend(
            [
                f"## {row['audit_id']} | {row['language']} | {row['work']} | {row['sample_id']}",
                "",
                f"**Question:** {row['question']}",
                "",
                f"**Gold answer:** {row['gold_answer']}",
                "",
                "**Evidence:**",
                "",
                row["evidence_text"],
                "",
            ]
        )
    (output_dir / "review_120.md").write_text("\n".join(review_lines), encoding="utf-8")

    batch_dir = output_dir / "review_batches"
    batch_dir.mkdir(exist_ok=True)
    for batch_index, start in enumerate(range(0, len(sampled), args.batch_size), start=1):
        batch_rows = sampled[start : start + args.batch_size]
        lines = [
            f"# Batch {batch_index}",
            "",
            f"- seed: `{args.seed}`",
            "",
        ]
        for row in batch_rows:
            lines.extend(
                [
                    f"## {row['audit_id']} | {row['language']} | {row['work']} | {row['sample_id']}",
                    "",
                    f"**Question:** {row['question']}",
                    "",
                    f"**Gold answer:** {row['gold_answer']}",
                    "",
                    "**Evidence:**",
                    "",
                    row["evidence_text"],
                    "",
                ]
            )
        path = batch_dir / f"batch_{batch_index:02d}.md"
        path.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": source.as_posix(),
        "source_sha256": sha256(source),
        "seed": args.seed,
        "population": len(rows),
        "sample": len(sampled),
        "per_work": args.per_work,
        "batch_size": args.batch_size,
        "population_by_language": dict(sorted(Counter(row["language"] for row in rows).items())),
        "sample_by_language": dict(sorted(Counter(row["language"] for row in sampled).items())),
        "sample_by_work": dict(sorted(Counter(row["work"] for row in sampled).items())),
    }
    (output_dir / "sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
