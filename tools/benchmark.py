"""
tools/benchmark.py
------------------
Phase 7: measures how long each model takes to load and to predict on THIS
laptop. The numbers go straight into the thesis (a deployment-feasibility
table) and they also tell you which model is realistic as the app default.

    python tools/benchmark.py
    python tools/benchmark.py --image path/to/leaf.jpg --runs 10 --csv results.csv

If no image is given, a neutral grey 224x224 image is used - fine for timing,
since inference time does not depend on the picture's content.
"""

import argparse
import csv
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

import config  # noqa: E402
from utils.model_loader import get_registry  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Time each model on this machine.")
    parser.add_argument("--image", help="Leaf photo to use (optional).")
    parser.add_argument("--runs", type=int, default=5,
                        help="Timed runs per model after one warm-up.")
    parser.add_argument("--csv", help="Write the table to this CSV file.")
    args = parser.parse_args()

    image = (Image.open(args.image) if args.image
             else Image.new("RGB", (224, 224), (128, 140, 128)))

    registry = get_registry()
    slugs = registry.available_slugs()

    if not slugs:
        print("No checkpoints found in model/. Nothing to benchmark.")
        return 2

    print("=" * 72)
    print(f"  Benchmark - device: {registry.device}, {args.runs} timed run(s) per model")
    print("=" * 72)
    print(f"  {'Model':<16}{'Size':>10}{'Load':>9}{'Mean':>11}{'Median':>11}{'Min':>10}{'Max':>10}")
    print("  " + "-" * 77)

    catalogue = {m["slug"]: m for m in registry.list_models()}
    rows = []

    for slug in slugs:
        registry.unload_all()  # measure a cold load, as the user experiences it

        load_started = time.perf_counter()
        registry.load(slug)
        load_s = time.perf_counter() - load_started

        registry.predict(slug, image)  # warm-up: first pass allocates buffers

        times = []
        for _ in range(args.runs):
            started = time.perf_counter()
            registry.predict(slug, image)
            times.append((time.perf_counter() - started) * 1000)

        meta = catalogue[slug]
        row = {
            "model": meta["name"],
            "slug": slug,
            "arch": meta["arch"],
            "size_mb": meta["size_mb"],
            "load_s": round(load_s, 2),
            "mean_ms": round(statistics.mean(times), 1),
            "median_ms": round(statistics.median(times), 1),
            "min_ms": round(min(times), 1),
            "max_ms": round(max(times), 1),
        }
        rows.append(row)

        print(f"  {row['model']:<16}{row['size_mb']:>7} MB{row['load_s']:>8.2f}s"
              f"{row['mean_ms']:>9.1f}ms{row['median_ms']:>9.1f}ms"
              f"{row['min_ms']:>8.1f}ms{row['max_ms']:>8.1f}ms")

    registry.unload_all()

    fastest = min(rows, key=lambda r: r["mean_ms"])
    lightest = min(rows, key=lambda r: r["size_mb"] or 1e9)
    print("\n  Fastest inference : " + f"{fastest['model']} ({fastest['mean_ms']} ms)")
    print("  Smallest file     : " + f"{lightest['model']} ({lightest['size_mb']} MB)")
    print(f"\n  Models kept in RAM at a time: {config.MAX_MODELS_IN_MEMORY} "
          "(config.MAX_MODELS_IN_MEMORY)")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Saved: {args.csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
