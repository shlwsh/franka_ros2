"""Export the Paper II KG stub to CSV edge lists."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KG = ROOT / "kg" / "kg_stub.json"
DEFAULT_OUT = ROOT / "kg" / "kg_edges.csv"


def export_edges(kg_path: Path = DEFAULT_KG, out_path: Path = DEFAULT_OUT) -> int:
    kg = json.loads(kg_path.read_text(encoding="utf-8"))
    rows = []
    for relation, sign in (("supports", 1), ("contradicts", -1)):
        for source, target, weight in kg.get(relation, []):
            rows.append(
                {
                    "source": source,
                    "target": target,
                    "relation": relation[:-1],
                    "weight": float(weight),
                    "signed_weight": sign * float(weight),
                }
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["source", "target", "relation", "weight", "signed_weight"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg", type=Path, default=DEFAULT_KG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    count = export_edges(args.kg, args.out)
    print(f"wrote {count} KG edges to {args.out}")


if __name__ == "__main__":
    main()
