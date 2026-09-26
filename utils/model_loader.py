"""
utils/model_loader.py
---------------------
Owns the five trained models: reads model/models.json, loads a checkpoint on
demand, keeps only a small number in memory, and runs predictions.

Why a registry instead of loading all five at startup:
VGG16-BN alone is roughly 528 MB of weights. Holding all five would make the
app slow to start and heavy on a student laptop. Instead the selected model is
loaded the first time it is used and kept; when the memory budget is exceeded,
the least-recently-used model is dropped. Compare mode simply walks the list
one model at a time.
"""

import json
import os
import threading
import time
from collections import OrderedDict

import torch
import torch.nn.functional as F

import config
import data_utils as du
from utils import preprocess as pp


class ModelNotFoundError(Exception):
    """Raised when a slug is not in models.json."""


class CheckpointMissingError(Exception):
    """Raised when models.json lists a model whose .pt file is not on disk."""


class ModelRegistry:
    def __init__(self, models_json: str = None, labels_json: str = None):
        self.models_json = models_json or config.MODELS_JSON
        self.labels_json = labels_json or config.LABELS_JSON

        self._lock = threading.Lock()
        self._loaded = OrderedDict()   # slug -> torch model (most recent last)
        self._load_times = {}          # slug -> seconds it took to load

        self.device = self._pick_device()
        self.classes, self.display_names = self._read_labels()
        self.entries = self._read_models()

        self._check_class_order()

    # -- setup -------------------------------------------------------------

    def _pick_device(self):
        if config.FORCE_CPU or not torch.cuda.is_available():
            return torch.device("cpu")
        return torch.device("cuda")

    def _read_labels(self):
        with open(self.labels_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        classes = data["classes"]
        display = data.get("display_names", {})
        return classes, {c: display.get(c, c) for c in classes}

    def _read_models(self):
        with open(self.models_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = OrderedDict()
        for m in data["models"]:
            slug = m["slug"]
            m = dict(m)
            m["checkpoint_path"] = os.path.join(config.MODEL_DIR, m["checkpoint"])
            entries[slug] = m

        self.default_slug = data.get("default") or next(iter(entries))
        if self.default_slug not in entries:
            self.default_slug = next(iter(entries))
        return entries

    def _check_class_order(self):
        """
        labels.json and data_utils.CLASSES must agree. If they ever drift, every
        prediction gets the wrong name attached while still looking confident,
        which is the nastiest kind of bug in this app - so we fail loudly at
        startup instead.
        """
        if list(self.classes) != list(du.CLASSES):
            raise RuntimeError(
                "Class order mismatch!\n"
                f"  model/labels.json : {self.classes}\n"
                f"  data_utils.CLASSES: {du.CLASSES}\n"
                "These must be identical and in training order. Fix one of them "
                "before using the app - otherwise predictions get wrong labels."
            )

    # -- catalogue ---------------------------------------------------------

    def list_models(self):
        """Everything the dropdown needs, including which checkpoints exist."""
        out = []
        for slug, m in self.entries.items():
            path = m["checkpoint_path"]
            available = os.path.isfile(path)
            size_mb = round(os.path.getsize(path) / (1024 * 1024), 1) if available else None
            out.append({
                "slug": slug,
                "name": m["name"],
                "arch": m["arch"],
                "img_size": m.get("img_size", du.IMG_SIZE),
                "notes": m.get("notes", ""),
                "available": available,
                "size_mb": size_mb,
                "loaded": slug in self._loaded,
                "load_seconds": self._load_times.get(slug),
            })
        return out

    def available_slugs(self):
        return [m["slug"] for m in self.list_models() if m["available"]]

    def get_entry(self, slug: str):
        if slug not in self.entries:
            raise ModelNotFoundError(
                f"Unknown model '{slug}'. Available: {list(self.entries)}"
            )
        return self.entries[slug]

    # -- loading -----------------------------------------------------------

    def _extract_state_dict(self, obj):
        """
        Accepts what torch.load() returns and digs out the weights.

        The training notebooks save a plain state_dict, but it is common to
        later save a richer checkpoint like
        {'model_state_dict': ..., 'epoch': ..., 'optimizer': ...}. Both are
        handled here, as is a checkpoint saved from a DataParallel model
        (keys prefixed with 'module.').
        """
        state = obj
        if isinstance(obj, dict):
            for key in ("model_state_dict", "state_dict", "model", "weights"):
                if key in obj and isinstance(obj[key], dict):
                    state = obj[key]
                    break

        if not isinstance(state, dict):
            raise CheckpointMissingError(
                "Checkpoint did not contain a state_dict. Save it with "
                "torch.save(model.state_dict(), path)."
            )

        if any(k.startswith("module.") for k in state.keys()):
            state = {k.replace("module.", "", 1): v for k, v in state.items()}
        return state

    def load(self, slug: str):
        """Loads a model if needed and returns it. Thread-safe."""
        entry = self.get_entry(slug)

        with self._lock:
            if slug in self._loaded:
                self._loaded.move_to_end(slug)  # mark as recently used
                return self._loaded[slug]

            path = entry["checkpoint_path"]
            if not os.path.isfile(path):
                raise CheckpointMissingError(
                    f"No checkpoint for '{slug}' at {path}. Copy "
                    f"{os.path.basename(path)} from Colab into "
                    f"model/{slug}/ and refresh."
                )

            started = time.perf_counter()

            # pretrained=False: the trained weights come from the checkpoint, so
            # the app never needs to download ImageNet weights. That is what lets
            # it run with the internet switched off.
            model = du.build_model(entry["arch"], num_classes=len(self.classes),
                                   pretrained=False)

            raw = torch.load(path, map_location="cpu", weights_only=False)
            state = self._extract_state_dict(raw)

            missing, unexpected = model.load_state_dict(state, strict=False)
            if missing or unexpected:
                raise CheckpointMissingError(
                    f"Checkpoint for '{slug}' does not match architecture "
                    f"'{entry['arch']}'.\n"
                    f"  missing keys   : {list(missing)[:5]}{'...' if len(missing) > 5 else ''}\n"
                    f"  unexpected keys: {list(unexpected)[:5]}{'...' if len(unexpected) > 5 else ''}\n"
                    "Usually this means the slug in models.json points at a "
                    "checkpoint trained with a different architecture."
                )

            model.to(self.device)
            model.eval()

            self._loaded[slug] = model
            self._load_times[slug] = round(time.perf_counter() - started, 2)
            self._evict_if_needed()

            return model

    def _evict_if_needed(self):
        """Drops least-recently-used models past the memory budget. Caller holds the lock."""
        budget = max(1, config.MAX_MODELS_IN_MEMORY)
        while len(self._loaded) > budget:
            old_slug, _ = self._loaded.popitem(last=False)
            self._load_times.pop(old_slug, None)
        if self.device.type == "cuda":
            torch.cuda.empty_cache()

    def unload_all(self):
        with self._lock:
            self._loaded.clear()
            self._load_times.clear()
            if self.device.type == "cuda":
                torch.cuda.empty_cache()

    # -- prediction --------------------------------------------------------

    def predict(self, slug: str, image, top_k: int = None):
        """
        Runs one model on one PIL image.

        Returns the predicted class, its confidence, the full probability
        distribution, the top-k list, and timings - everything the result
        card and the comparison table need.
        """
        top_k = top_k or config.TOP_K
        entry = self.get_entry(slug)

        load_started = time.perf_counter()
        model = self.load(slug)
        load_ms = (time.perf_counter() - load_started) * 1000

        tensor = pp.preprocess_image(
            image,
            img_size=entry.get("img_size", du.IMG_SIZE),
            preprocess=entry.get("preprocess", "imagenet_224"),
        ).to(self.device)

        started = time.perf_counter()
        with torch.no_grad():
            outputs = model(tensor)
            if isinstance(outputs, tuple):   # defensive, mirrors data_utils
                outputs = outputs[0]
            probs = F.softmax(outputs, dim=1).cpu().numpy()[0]
        predict_ms = (time.perf_counter() - started) * 1000

        pred_idx = int(probs.argmax())
        pred_class = self.classes[pred_idx]
        confidence = float(probs[pred_idx])

        ranked = sorted(
            ({"class": c,
              "display": self.display_names.get(c, c),
              "probability": float(p)}
             for c, p in zip(self.classes, probs)),
            key=lambda d: -d["probability"],
        )

        return {
            "model": slug,
            "model_name": entry["name"],
            "predicted_class": pred_class,
            "display_name": self.display_names.get(pred_class, pred_class),
            "confidence": confidence,
            "low_confidence": confidence < config.LOW_CONFIDENCE_THRESHOLD,
            "threshold": config.LOW_CONFIDENCE_THRESHOLD,
            "top_k": ranked[:top_k],
            "probabilities": {r["class"]: r["probability"] for r in ranked},
            "predict_ms": round(predict_ms, 1),
            "load_ms": round(load_ms, 1),
            "device": str(self.device),
        }

    def predict_all(self, image, slugs=None, top_k: int = None):
        """
        Compare mode: the same image through every available model, one at a
        time. A model that fails (missing checkpoint, say) is reported in the
        row instead of breaking the whole comparison.
        """
        slugs = slugs or self.available_slugs()
        results = []
        for slug in slugs:
            try:
                results.append(self.predict(slug, image, top_k=top_k))
            except Exception as exc:
                results.append({
                    "model": slug,
                    "model_name": self.entries.get(slug, {}).get("name", slug),
                    "error": str(exc),
                })
        return results


# A single shared registry for the whole app.
_registry = None
_registry_lock = threading.Lock()


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = ModelRegistry()
    return _registry
