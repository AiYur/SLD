# Sweet Diagnosis — Sugarcane Leaf Disease Detection

A web app that identifies sugarcane leaf diseases from a photo. It runs **fully offline on a laptop**: the browser is only the interface, while the five trained PyTorch models run locally in Python. Any of the five models can be selected from the page, or all of them compared side by side on the same image.

---

## Important: what changed from the original plan

The first draft of this plan assumed Keras models with three different preprocessing styles and an alphabetical class order. Your `data_utils.py` says otherwise, and the app is built to match your actual training code:

| Item | Planned | Actual (from `data_utils.py`) |
|------|---------|-------------------------------|
| Framework | TensorFlow / Keras | **PyTorch + torchvision** |
| Class order | Alphabetical (Dry first) | **`Healthy, Mosaic, RedRot, Rust, Yellow, Dry`** — not alphabetical |
| Preprocessing | Three styles (caffe / torch / built-in) | **One style for all five**: `Resize(224,224) → ToTensor → ImageNet normalize` |
| Checkpoints | `.keras` files | **`.pt` state dicts** at `checkpoints/<slug>/<slug>_best.pt` |

That last row is why the app imports your `data_utils.py` rather than re-implementing anything: the same `get_eval_transforms()` and `build_model()` that trained the models also serve them.

> **The class order is the single most dangerous detail in this project.** Index 0 is `Healthy`, not `Dry`. If anything ever sorts that list, every prediction gets a wrong label while still looking confident. The app refuses to start if `model/labels.json` and `data_utils.CLASSES` disagree.

---

## Classes

| Index | Class | Shown as |
|-------|-------|----------|
| 0 | Healthy | Healthy |
| 1 | Mosaic | Mosaic Virus |
| 2 | RedRot | Red Rot |
| 3 | Rust | Rust |
| 4 | Yellow | Yellow Leaf |
| 5 | Dry | Dry / Withered |

## Models

All five are ImageNet-pretrained torchvision CNNs with a 6-class head, trained through the shared pipeline in `data_utils.py`.

| Slug | Model | Architecture | Approx. size |
|------|-------|--------------|--------------|
| `convnext` | ConvNeXt-Tiny | `convnext_tiny` | ~110 MB |
| `efficientnet` | EfficientNet-B0 | `efficientnet_b0` | ~16 MB |
| `resnet` | ResNet50 | `resnet50` | ~90 MB |
| `densenet` | DenseNet121 | `densenet121` | ~27 MB |
| `vgg` | VGG16-BN | `vgg16_bn` | ~528 MB |

Only one model is held in memory at a time (`config.MAX_MODELS_IN_MEMORY`), so a student laptop is never asked to hold all five at once.

---

## Quick start

```bash
# 1. Install dependencies (CPU-only PyTorch is much smaller — do this first)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 2. Put your trained checkpoints in place (see Phase 1 / Phase 2 below)
#    model/resnet/resnet_best.pt, model/vgg/vgg_best.pt, ...

# 3. Run it
python app.py          # then open http://127.0.0.1:5000
```

No checkpoints yet? Generate placeholders to try the interface — the predictions are random, only the plumbing is real:

```bash
python tools/make_dummy_models.py efficientnet densenet
```

`run_app.sh` (macOS/Linux, `chmod +x` it once) and `run_app.bat` (Windows) start the app with a double-click.

---

## Project structure

```
sugarcane-leaf-app/
├── app.py                      # Flask server: pages + JSON API
├── config.py                   # all settings in one place
├── data_utils.py               # inference subset of your training file (class order, transforms, build_model)
├── requirements.txt
├── run_app.sh / run_app.bat    # double-click launchers
│
├── model/
│   ├── models.json             # the five models: slug, arch, checkpoint path, input size
│   ├── labels.json             # class order (must match data_utils.CLASSES)
│   ├── convnext/  densenet/  efficientnet/  resnet/  vgg/     <- *_best.pt goes here
│   └── parity_reference.json   # (from Colab) what each model predicted there
│
├── utils/
│   ├── preprocess.py           # calls data_utils.get_eval_transforms() — no re-implementation
│   ├── model_loader.py         # loads/swaps models, runs predictions, guards the class order
│   ├── disease_info.py         # per-class notes and next steps (English + Filipino)
│   └── history.py              # SQLite scan history
│
├── templates/index.html
├── static/
│   ├── css/style.css
│   ├── js/main.js              # upload, camera, model picker, compare table, history
│   ├── images/favicon.svg
│   └── vendor/                 # local copies of any future libraries (keep it CDN-free)
│
├── tools/
│   ├── make_dummy_models.py    # placeholder checkpoints for testing the app
│   ├── parity_check.py         # app predictions vs Colab predictions
│   └── benchmark.py            # load time and inference time per model, on this laptop
│
├── training/
│   ├── export_for_app.ipynb    # Phase 1, run in Colab
│   └── export_for_app.py       # same thing as a plain script
│
├── data/history.db             # created on first scan
└── uploads/                    # only used if SWEET_SAVE_UPLOADS=1
```

---

## Build phases

### Phase 1 — Evaluate and export (in Colab) ✅ script ready

Open `training/export_for_app.ipynb` in Colab, point `PROJECT_ROOT` at your Drive folder, and run it. It:

- evaluates all five checkpoints on the **same** test split (accuracy, macro precision/recall/F1, confusion matrix)
- writes `results_summary.csv` and a confusion-matrix image per model — the Chapter 4 table
- assembles `app_bundle/` with the checkpoints, `labels.json`, and a `models.json` whose default is the best model by macro F1
- writes `parity_reference.json` plus the sample images it used
- zips the bundle for download

**Done when:** `app_bundle.zip` is on your laptop.

### Phase 2 — Project setup ✅ done

Unzip `app_bundle.zip` and copy its contents into this project:

- the five folders and both JSON files → `model/`
- `parity_images/` → `training/parity_images/`

Then `python app.py`. The startup banner lists every model as `[ok]` or `[missing]`.

**Done when:** all five show `[ok]`.

### Phase 3 — Backend ✅ done

`utils/model_loader.py` reads `models.json`, loads a checkpoint on demand, keeps one model in RAM, and runs predictions. Endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | server state, device, preprocessing summary |
| `GET /api/models` | the model list for the dropdown |
| `POST /api/predict` | one image, one model |
| `POST /api/compare` | one image, every available model |
| `GET /api/disease/<class>` | notes for a class (`?lang=fil` for Filipino) |
| `GET /api/history` · `DELETE` | scan history |
| `GET /api/history/export` | history as CSV |

Handled explicitly: missing checkpoint (503 with the exact path to fix), unknown model slug (404), non-image upload, oversized upload, EXIF-rotated phone photos, and an architecture/checkpoint mismatch.

### Phase 4 — Frontend ✅ done

Drag-and-drop or browse, webcam capture, image preview, model dropdown (with file sizes), confidence ring, top-3 bars, per-model timings, and a low-confidence warning below 60% (`config.LOW_CONFIDENCE_THRESHOLD`). Disease notes appear under every result.

### Phase 5 — Compare all ✅ done

One button runs the image through every available model and shows a table of prediction, confidence, and inference time. The banner states whether the models were unanimous, split, or in complete disagreement, and the table can be exported as CSV for the thesis.

### Phase 6 — Offline hardening ✅ done

No CDN links, no web fonts, no analytics — the page uses the system font stack and inline SVG icons. `build_model(..., pretrained=False)` means the app never downloads ImageNet weights. To confirm: turn off Wi-Fi, then run `python app.py` and use it normally.

To let phones on the same Wi-Fi or hotspot use the laptop's app, start it with `SWEET_HOST=0.0.0.0 python app.py` and open the address printed in the banner.

### Phase 7 — Testing and validation ⬜ needs your real checkpoints

```bash
python tools/parity_check.py     # app predictions vs Colab predictions
python tools/benchmark.py --csv results/benchmark.csv
```

`parity_check.py` is the important one. It re-runs the exact images from `parity_reference.json` and compares full probability vectors. If they match, the app's preprocessing is provably identical to Colab's — the most common way a good model goes wrong after deployment.

Also worth testing by hand: photos in different lighting, a blurry photo, and a non-leaf photo (which should trip the low-confidence warning, since the model always returns one of the six classes).

### Phase 8 — Polish ✅ done

Disease information panel, SQLite scan history with thumbnails and CSV export, and an English/Filipino toggle.

---

## Configuration

Everything lives in `config.py`, and the common ones can be set as environment variables:

| Variable | Default | Meaning |
|----------|---------|---------|
| `SWEET_HOST` | `127.0.0.1` | `0.0.0.0` also serves phones on the same Wi-Fi |
| `SWEET_PORT` | `5000` | port |
| `SWEET_MAX_MODELS` | `1` | models kept in RAM at once |
| `SWEET_FORCE_CPU` | `0` | `1` to ignore a GPU |
| `SWEET_SAVE_UPLOADS` | `0` | `1` keeps a copy of every uploaded image |
| `SWEET_DEBUG` | `0` | `1` for Flask's auto-reloading debug server |

Other useful settings: `LOW_CONFIDENCE_THRESHOLD` (0.60), `TOP_K` (3), `HISTORY_LIMIT` (200).

---

## Database

**Not required.** Models and labels are plain files, and a prediction stores nothing by itself.

Scan history uses **SQLite** (`data/history.db`): one file, built into Python, no server, works offline. Delete the file to reset it, or set `ENABLE_HISTORY = False` in `config.py` to turn the feature off. An online database (Firebase, Supabase) would only be needed to collect scans from many devices — not the case here.

---

## Troubleshooting

**"Checkpoint for 'x' does not match architecture"** — `models.json` points that slug at a checkpoint trained with a different architecture, or your torchvision version differs enough from Colab's to rename internal layers. Check the slug first, then pin torchvision to Colab's version.

**"Class order mismatch!" at startup** — `model/labels.json` and `data_utils.CLASSES` disagree. Make them identical, in training order. The app stops here on purpose.

**Predictions differ from Colab** — run `tools/parity_check.py`. It almost always comes down to preprocessing or class order.

**Slow first prediction** — that is the model loading (0.2–3 s depending on size). Later predictions on the same model reuse it. Switching models drops the previous one, so the next switch pays the load cost again; raise `SWEET_MAX_MODELS` to 2 or 3 if the laptop has the RAM.

**The install is enormous** — you installed the CUDA build of PyTorch. Uninstall and reinstall from the CPU index (see Quick start).

---

## Future option: running on phones in the field

Not used here, but a realistic next step if farmers need this on their own phones.

Convert one model to ONNX and run it in the browser with ONNX Runtime Web, wrapped as a Progressive Web App so it caches and works with no signal. Hosting would be free (GitHub Pages, Netlify), and each phone does its own processing.

| Factor | Local Python (current) | Browser-based (future) |
|--------|------------------------|------------------------|
| Runs on | This laptop, and devices on its Wi-Fi | Any phone browser |
| Works offline | Yes | Yes, after the first visit |
| Model conversion | Not needed | Needed per model |
| All five models | Easy | Heavy — VGG alone is ~528 MB |
| Development effort | Lower | Higher (preprocessing rebuilt in JavaScript) |

EfficientNet-B0 is the obvious candidate: smallest file, fastest inference, and it converts cleanly. ConvNeXt is the one to expect trouble from.

---

## Status

- [x] Five models trained (ConvNeXt, EfficientNet, ResNet, DenseNet, VGG)
- [x] Phase 1 — export/evaluation notebook written (run it in Colab)
- [x] Phase 2 — project structure
- [x] Phase 3 — backend and API
- [x] Phase 4 — frontend
- [x] Phase 5 — compare-all mode
- [x] Phase 6 — offline hardening
- [ ] Phase 7 — parity check and benchmark **with the real checkpoints**
- [x] Phase 8 — disease info, history, Filipino toggle
