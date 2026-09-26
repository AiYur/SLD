# %% [markdown]
# # Phase 1 — Evaluate the five models and export them for the web app
#
# Run this in **Google Colab**, in the same Drive project the training
# notebooks used. It does four things, in one pass:
#
# 1. Evaluates all five trained checkpoints on the **same** test split
#    (accuracy, macro precision/recall/F1, confusion matrix).
# 2. Builds `results_summary.csv` — the comparison table for Chapter 4.
# 3. Assembles an `app_bundle/` folder holding the checkpoints,
#    `labels.json`, and a `models.json` whose default is the best model.
# 4. Writes `parity_reference.json` + a few test images, so
#    `tools/parity_check.py` can later prove the laptop app reproduces
#    exactly what Colab predicted.
#
# At the end it zips the bundle for download. Unzip it into the app's
# `model/` folder and Phase 2 is done.

# %%
from google.colab import drive
drive.mount('/content/drive')

# %%
import json
import os
import shutil
import sys

PROJECT_ROOT = '/content/drive/MyDrive/sweet_diagnosis'   # <- same path the training notebooks used
sys.path.append(PROJECT_ROOT)

import data_utils as du
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

SPLIT_PATH   = os.path.join(PROJECT_ROOT, 'split.json')
CKPT_ROOT    = os.path.join(PROJECT_ROOT, 'checkpoints')
RESULTS_DIR  = os.path.join(PROJECT_ROOT, 'results')
BUNDLE_DIR   = os.path.join(PROJECT_ROOT, 'app_bundle')
PARITY_N     = 6          # how many test images to record for the parity check

os.makedirs(RESULTS_DIR, exist_ok=True)

print('Device :', device)
print('Classes:', du.CLASSES, '  <- this exact order goes into the app')
print('Models :', du.MODEL_FAMILIES)

# %% [markdown]
# ## 1. Evaluate every model on the shared test split
#
# Every model is scored with the same `evaluate_model()` and the same test
# set, which is what makes the comparison fair.

# %%
split = du.load_split(SPLIT_PATH)
_, _, test_loader = du.make_dataloaders(split, batch_size=32, num_workers=2)
print(f'Test images: {len(split["test"])}')

all_metrics = {}

for slug, arch in du.MODEL_FAMILIES.items():
    ckpt = os.path.join(CKPT_ROOT, slug, f'{slug}_best.pt')
    if not os.path.isfile(ckpt):
        print(f'[skip] {slug:<13} no checkpoint at {ckpt}')
        continue

    print(f'\n=== {slug} ({arch}) ===')
    model = du.build_model(arch, num_classes=len(du.CLASSES), pretrained=False)
    model.load_state_dict(torch.load(ckpt, map_location=device))
    model = model.to(device)

    metrics = du.evaluate_model(model, test_loader, device)
    all_metrics[slug] = metrics

    print(metrics['classification_report'])
    du.save_results(metrics, os.path.join(RESULTS_DIR, f'{slug}_results.json'), slug)

    del model
    if device.type == 'cuda':
        torch.cuda.empty_cache()

# %% [markdown]
# ## 2. Comparison table
#
# This is the table that decides the app's default model, and the one that
# goes into the thesis.

# %%
import pandas as pd

rows = []
for slug, m in all_metrics.items():
    ckpt = os.path.join(CKPT_ROOT, slug, f'{slug}_best.pt')
    rows.append({
        'model': slug,
        'architecture': du.MODEL_FAMILIES[slug],
        'accuracy': round(m['accuracy'], 4),
        'precision_macro': round(m['precision_macro'], 4),
        'recall_macro': round(m['recall_macro'], 4),
        'f1_macro': round(m['f1_macro'], 4),
        'size_mb': round(os.path.getsize(ckpt) / (1024 * 1024), 1),
    })

summary = pd.DataFrame(rows).sort_values('f1_macro', ascending=False)
summary.to_csv(os.path.join(RESULTS_DIR, 'results_summary.csv'), index=False)
display(summary)

BEST_SLUG = summary.iloc[0]['model'] if len(summary) else 'resnet'
print(f'\nBest by macro F1: {BEST_SLUG} -> this becomes the app default.')

# %% [markdown]
# ## 3. Per-class confusion, for the diseases that get mixed up
#
# Overall accuracy hides the interesting part. If Rust and RedRot are being
# confused, that is what the defense panel will ask about.

# %%
import matplotlib.pyplot as plt
import numpy as np

for slug, m in all_metrics.items():
    cm = np.array(m['confusion_matrix'])
    cm_pct = cm / np.clip(cm.sum(axis=1, keepdims=True), 1, None)

    fig, ax = plt.subplots(figsize=(5.5, 4.6))
    ax.imshow(cm_pct, cmap='Greens', vmin=0, vmax=1)
    ax.set_xticks(range(len(du.CLASSES)), du.CLASSES, rotation=45, ha='right')
    ax.set_yticks(range(len(du.CLASSES)), du.CLASSES)
    ax.set_xlabel('Predicted'); ax.set_ylabel('Actual')
    ax.set_title(f'{slug} — confusion (row-normalized)')
    for i in range(len(du.CLASSES)):
        for j in range(len(du.CLASSES)):
            ax.text(j, i, cm[i, j], ha='center', va='center',
                    color='white' if cm_pct[i, j] > 0.5 else '#333', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f'{slug}_confusion.png'), dpi=150)
    plt.show()

# %% [markdown]
# ## 4. Build the app bundle
#
# Copies each checkpoint plus the two JSON files the app reads. The
# `preprocess` field is `imagenet_224` for every model because all five were
# trained with `data_utils.get_eval_transforms()`.

# %%
MODEL_META = {
    'convnext':     ('ConvNeXt-Tiny',   'Modern CNN design; usually the strongest accuracy of the five.'),
    'efficientnet': ('EfficientNet-B0', 'Best accuracy-per-megabyte; smallest checkpoint.'),
    'resnet':       ('ResNet50',        'Reliable baseline; fast and well understood.'),
    'densenet':     ('DenseNet121',     'Compact and accurate; dense feature reuse.'),
    'vgg':          ('VGG16-BN',        'Classic deep CNN; largest file and slowest of the five.'),
}

if os.path.exists(BUNDLE_DIR):
    shutil.rmtree(BUNDLE_DIR)
os.makedirs(BUNDLE_DIR)

entries = []
for slug in du.MODEL_FAMILIES:
    src = os.path.join(CKPT_ROOT, slug, f'{slug}_best.pt')
    if not os.path.isfile(src):
        print(f'[skip] {slug}: no checkpoint')
        continue

    os.makedirs(os.path.join(BUNDLE_DIR, slug), exist_ok=True)
    dst = os.path.join(BUNDLE_DIR, slug, f'{slug}_best.pt')
    shutil.copy2(src, dst)

    name, notes = MODEL_META[slug]
    entries.append({
        'slug': slug,
        'name': name,
        'arch': du.MODEL_FAMILIES[slug],
        'checkpoint': f'{slug}/{slug}_best.pt',
        'img_size': du.IMG_SIZE,
        'preprocess': 'imagenet_224',
        'notes': notes,
    })
    print(f'[copied] {slug:<13} {os.path.getsize(dst)/(1024*1024):7.1f} MB')

with open(os.path.join(BUNDLE_DIR, 'labels.json'), 'w') as f:
    json.dump({
        '_comment': 'Class order exactly as trained (data_utils.CLASSES). NOT alphabetical.',
        'classes': du.CLASSES,
        'display_names': {
            'Healthy': 'Healthy', 'Mosaic': 'Mosaic Virus', 'RedRot': 'Red Rot',
            'Rust': 'Rust', 'Yellow': 'Yellow Leaf', 'Dry': 'Dry / Withered',
        },
    }, f, indent=2)

with open(os.path.join(BUNDLE_DIR, 'models.json'), 'w') as f:
    json.dump({
        '_comment': "Generated by training/export_for_app.py. 'default' is the best model by macro F1.",
        'default': BEST_SLUG,
        'models': entries,
    }, f, indent=2)

print(f'\nBundle ready: {BUNDLE_DIR}  (default model: {BEST_SLUG})')

# %% [markdown]
# ## 5. Parity reference
#
# Records what each model predicted for a few specific test images, with full
# probabilities. Back on the laptop, `tools/parity_check.py` re-runs the same
# images and compares. If the numbers match, the app's preprocessing is
# provably identical to Colab's — the single most common way a working model
# goes wrong after deployment.

# %%
import torch.nn.functional as F
from PIL import Image

PARITY_IMG_DIR = os.path.join(BUNDLE_DIR, 'parity_images')
os.makedirs(PARITY_IMG_DIR, exist_ok=True)

# Spread the sample across classes rather than taking the first N.
by_class = {}
for path, label in split['test']:
    by_class.setdefault(label, []).append(path)

sample_paths = []
for label in sorted(by_class):
    sample_paths.extend(by_class[label][:max(1, PARITY_N // len(du.CLASSES))])
sample_paths = sample_paths[:PARITY_N]

transform = du.get_eval_transforms()
predictions = []

for slug, arch in du.MODEL_FAMILIES.items():
    ckpt = os.path.join(CKPT_ROOT, slug, f'{slug}_best.pt')
    if not os.path.isfile(ckpt):
        continue

    model = du.build_model(arch, num_classes=len(du.CLASSES), pretrained=False)
    model.load_state_dict(torch.load(ckpt, map_location=device))
    model = model.to(device).eval()

    for src in sample_paths:
        fname = os.path.basename(src)
        dst = os.path.join(PARITY_IMG_DIR, fname)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

        image = Image.open(src).convert('RGB')
        tensor = transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            probs = F.softmax(model(tensor), dim=1).cpu().numpy()[0]

        predictions.append({
            'model': slug,
            'image': fname,
            'predicted_class': du.CLASSES[int(probs.argmax())],
            'confidence': float(probs.max()),
            'probabilities': {c: float(p) for c, p in zip(du.CLASSES, probs)},
        })

    del model
    if device.type == 'cuda':
        torch.cuda.empty_cache()

with open(os.path.join(BUNDLE_DIR, 'parity_reference.json'), 'w') as f:
    json.dump({
        'classes': du.CLASSES,
        'img_size': du.IMG_SIZE,
        'normalize_mean': du.IMAGENET_MEAN,
        'normalize_std': du.IMAGENET_STD,
        'torch_version': torch.__version__,
        'predictions': predictions,
    }, f, indent=2)

print(f'Parity reference: {len(predictions)} predictions over {len(sample_paths)} images.')

# %% [markdown]
# ## 6. Download
#
# Unzip `app_bundle.zip` and copy its contents into the app's `model/`
# folder, and `parity_images/` into the app's `training/parity_images/`.

# %%
shutil.make_archive(os.path.join(PROJECT_ROOT, 'app_bundle'), 'zip', BUNDLE_DIR)
print('Created', os.path.join(PROJECT_ROOT, 'app_bundle.zip'))

from google.colab import files
files.download(os.path.join(PROJECT_ROOT, 'app_bundle.zip'))
