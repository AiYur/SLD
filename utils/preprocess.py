"""
utils/preprocess.py
-------------------
Turns an uploaded image into the exact tensor the trained models expect.

This is the single most important file for correctness. If the app's
preprocessing drifts even slightly from the Colab eval transform, every
model will still return confident answers - they will just be the wrong
ones. So instead of re-implementing the steps here, we call
`data_utils.get_eval_transforms()`, the very function the training
notebooks used for their validation and test sets:

    Resize((224, 224)) -> ToTensor() -> Normalize(ImageNet mean/std)

One transform covers all five models, because every model in this study was
trained on ImageNet-normalized 224x224 inputs.
"""

import io

from PIL import Image, ImageOps

import config
import data_utils as du

# Built once and reused. torchvision transforms are stateless, so sharing a
# single instance across requests is safe.
_TRANSFORM_CACHE = {}


def get_transform(img_size: int = None, preprocess: str = "imagenet_224"):
    """Returns (and caches) the eval transform for a given input size."""
    if img_size is None:
        img_size = du.IMG_SIZE

    if preprocess != "imagenet_224":
        raise ValueError(
            f"Unknown preprocess style '{preprocess}'. This study trained every "
            f"model with data_utils.get_eval_transforms(), i.e. 'imagenet_224'. "
            f"If you add a model with different preprocessing, add its branch here."
        )

    key = (preprocess, img_size)
    if key not in _TRANSFORM_CACHE:
        _TRANSFORM_CACHE[key] = du.get_eval_transforms(img_size)
    return _TRANSFORM_CACHE[key]


def load_image(file_bytes: bytes) -> Image.Image:
    """
    Opens uploaded bytes as an RGB PIL image.

    Three things happen here that matter in practice:
      * EXIF transpose - phone photos carry a rotation flag. Without this a
        sideways photo reaches the model sideways.
      * convert('RGB') - matches training, and drops the alpha channel that
        PNG screenshots carry.
      * a size cap - a 12MP photo is downscaled first so we are not resizing
        a huge array down to 224x224 in one step (slow and memory-hungry).
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except Exception as exc:
        raise ValueError(f"That file could not be opened as an image ({exc}).")

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    max_dim = config.MAX_IMAGE_DIMENSION
    if max(image.size) > max_dim:
        image.thumbnail((max_dim, max_dim), Image.LANCZOS)

    return image


def preprocess_image(image: Image.Image, img_size: int = None,
                     preprocess: str = "imagenet_224"):
    """PIL image -> normalized tensor of shape (1, 3, H, W), ready for the model."""
    transform = get_transform(img_size, preprocess)
    tensor = transform(image)
    return tensor.unsqueeze(0)  # add the batch dimension


def bytes_to_tensor(file_bytes: bytes, img_size: int = None,
                    preprocess: str = "imagenet_224"):
    """Convenience: uploaded bytes straight to a model-ready tensor."""
    return preprocess_image(load_image(file_bytes), img_size, preprocess)


def describe_pipeline() -> dict:
    """Small summary shown on the app's About panel, and used by parity_check."""
    return {
        "resize": f"{du.IMG_SIZE}x{du.IMG_SIZE} (square, no crop)",
        "color": "RGB",
        "scale": "ToTensor -> 0.0-1.0",
        "normalize_mean": du.IMAGENET_MEAN,
        "normalize_std": du.IMAGENET_STD,
        "source": "data_utils.get_eval_transforms()",
    }
