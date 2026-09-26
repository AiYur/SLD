"""
tools/make_dummy_models.py
--------------------------
Creates placeholder checkpoints with RANDOM weights so the app can be tested
before the real Colab checkpoints are copied in.

Why this exists: the frontend, the model registry, compare mode, history, and
the whole request path can all be exercised without waiting on trained
weights. The predictions are meaningless - that is the point; only the
plumbing is being checked.

    python tools/make_dummy_models.py                    # all five
    python tools/make_dummy_models.py efficientnet densenet
    python tools/make_dummy_models.py --force            # overwrite existing

SAFETY: it refuses to overwrite an existing checkpoint unless --force is
given, so it can never destroy your real trained weights by accident.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch  # noqa: E402

import config  # noqa: E402
import data_utils as du  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Generate random-weight test checkpoints.")
    parser.add_argument("slugs", nargs="*", help="Model slugs to build (default: all).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing checkpoint files.")
    args = parser.parse_args()

    with open(config.MODELS_JSON, "r", encoding="utf-8") as f:
        catalogue = json.load(f)["models"]

    wanted = args.slugs or [m["slug"] for m in catalogue]
    entries = [m for m in catalogue if m["slug"] in wanted]

    unknown = set(wanted) - {m["slug"] for m in catalogue}
    if unknown:
        print(f"Unknown slug(s): {', '.join(sorted(unknown))}")
        return 1

    print("Creating placeholder checkpoints (RANDOM weights - for testing only)\n")

    for entry in entries:
        path = os.path.join(config.MODEL_DIR, entry["checkpoint"])
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.exists(path) and not args.force:
            print(f"  [skip]  {entry['slug']:<13} already exists - use --force to replace")
            continue

        model = du.build_model(entry["arch"], num_classes=len(du.CLASSES),
                               pretrained=False)
        torch.save(model.state_dict(), path)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  [made]  {entry['slug']:<13} {entry['arch']:<16} {size_mb:7.1f} MB")

    print("\nDone. Start the app with: python app.py")
    print("Replace these files with your real *_best.pt checkpoints from Colab "
          "before trusting any prediction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
