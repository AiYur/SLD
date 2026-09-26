"""
tools/parity_check.py
---------------------
Phase 7's most important test: does the app predict the same thing Colab did?

The Colab export notebook writes `parity_reference.json` - the predictions
each trained model made on a handful of test images, together with the class
probabilities. This script re-runs those same images through the app's own
code path (utils/preprocess + utils/model_loader) and compares.

    python tools/parity_check.py
    python tools/parity_check.py --reference model/parity_reference.json --tolerance 1e-4

A mismatch almost always means preprocessing drift: a different resize, a
missing normalization, BGR vs RGB, or a class list that got sorted somewhere.
Those bugs are invisible in the UI - the app looks confident and is simply
wrong - which is exactly why this check exists.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import data_utils as du  # noqa: E402
from utils import preprocess as pp  # noqa: E402
from utils.model_loader import get_registry  # noqa: E402

DEFAULT_REFERENCE = os.path.join(config.MODEL_DIR, "parity_reference.json")


def main():
    parser = argparse.ArgumentParser(description="Compare app predictions against Colab.")
    parser.add_argument("--reference", default=DEFAULT_REFERENCE,
                        help="parity_reference.json exported from Colab.")
    parser.add_argument("--images", default=os.path.join(config.BASE_DIR, "training", "parity_images"),
                        help="Folder holding the same images the reference used.")
    parser.add_argument("--tolerance", type=float, default=1e-3,
                        help="Max allowed absolute difference in probability.")
    args = parser.parse_args()

    print("=" * 66)
    print("  Parity check - app vs Colab")
    print("=" * 66)

    pipeline = pp.describe_pipeline()
    print("\n  App preprocessing:")
    for key, value in pipeline.items():
        print(f"    {key:<16} {value}")
    print(f"\n  Class order: {du.CLASSES}")

    if not os.path.isfile(args.reference):
        print(f"\n  No reference file at {args.reference}")
        print("  Run the export notebook in Colab (training/export_for_app.py) to")
        print("  produce parity_reference.json, then copy it into model/.")
        return 2

    with open(args.reference, "r", encoding="utf-8") as f:
        reference = json.load(f)

    ref_classes = reference.get("classes")
    if ref_classes and list(ref_classes) != list(du.CLASSES):
        print("\n  [FAIL] Class order differs between Colab and this app:")
        print(f"    Colab: {ref_classes}")
        print(f"    App  : {du.CLASSES}")
        return 1

    registry = get_registry()
    from PIL import Image

    total = passed = skipped = 0
    worst = 0.0
    failures = []

    for item in reference.get("predictions", []):
        slug = item["model"]
        image_name = item["image"]
        image_path = os.path.join(args.images, image_name)

        if not os.path.isfile(image_path):
            print(f"  [skip] {slug:<13} {image_name} - image not found in {args.images}")
            skipped += 1
            continue

        if slug not in registry.available_slugs():
            print(f"  [skip] {slug:<13} {image_name} - checkpoint not in model/")
            skipped += 1
            continue

        total += 1
        result = registry.predict(slug, Image.open(image_path))

        ref_probs = item["probabilities"]
        diff = max(abs(result["probabilities"][c] - ref_probs[c]) for c in du.CLASSES)
        worst = max(worst, diff)

        same_class = result["predicted_class"] == item["predicted_class"]
        close = diff <= args.tolerance

        if same_class and close:
            passed += 1
            print(f"  [ok]   {slug:<13} {image_name:<28} {result['predicted_class']:<9} "
                  f"max Δp={diff:.2e}")
        else:
            failures.append((slug, image_name, item["predicted_class"],
                             result["predicted_class"], diff))
            print(f"  [FAIL] {slug:<13} {image_name:<28} "
                  f"colab={item['predicted_class']} app={result['predicted_class']} "
                  f"max Δp={diff:.2e}")

    print("\n" + "-" * 66)
    print(f"  {passed}/{total} matched   ({skipped} skipped)   worst Δp = {worst:.2e}")

    if failures:
        print("\n  Mismatches found. Check, in this order:")
        print("    1. data_utils.CLASSES matches the training file exactly (order!)")
        print("    2. get_eval_transforms() is unchanged: Resize(224,224) -> ToTensor -> Normalize")
        print("    3. models.json points each slug at the right architecture")
        print("    4. torch / torchvision versions roughly match Colab's")
        return 1

    if total == 0:
        print("\n  Nothing was compared. Copy the parity images into "
              f"{args.images} and the checkpoints into model/.")
        return 2

    print("\n  Parity confirmed - the app reproduces Colab's predictions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
