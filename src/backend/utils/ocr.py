"""Extract room-number candidates from photos without deciding game outcomes."""

import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_PIXELS = 20_000_000
MIN_CONFIDENCE = 0.8
ROOM_NUMBER = re.compile(r"(?<![\w.-])(?:EME\s+[0-9]{4}|"
                         r"(?:UNC|FIP|COM|ASC|ART|CCS|ADM|SCI|LIB)\s+[0-9]{3})(?![\w.-])", re.ASCII)
_lock = Lock()


class InvalidPhoto(ValueError):
    """The photo cannot be safely decoded."""


class OCRUnavailable(RuntimeError):
    """The OCR runtime or model is unavailable."""


@lru_cache(maxsize=1)
def _get_engine():
    from paddleocr import PaddleOCR

    return PaddleOCR(device="cpu",
                     text_detection_model_name="PP-OCRv5_mobile_det",
                     text_recognition_model_name="en_PP-OCRv5_mobile_rec",
                     use_doc_orientation_classify=False, use_doc_unwarping=False,
                     use_textline_orientation=True)


def _save_photo(photo, path):
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(BytesIO(photo)) as image:
            if image.format not in {"JPEG", "PNG"} or image.width * image.height > MAX_PHOTO_PIXELS:
                raise InvalidPhoto("Use a JPEG or PNG photo with at most 20 million pixels.")
            ImageOps.exif_transpose(image).convert("RGB").save(path)
    except InvalidPhoto:
        raise
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise InvalidPhoto("The photo could not be read. Please retake it.") from exc


def extract_room_numbers(photo: bytes) -> list[str]:
    """Return distinct high-confidence candidates; [] means no readable room number."""
    if not isinstance(photo, bytes) or not photo or len(photo) > MAX_PHOTO_BYTES:
        raise InvalidPhoto("Provide a non-empty photo of at most 5 MiB.")
    try:
        with TemporaryDirectory(prefix="lit-ocr-") as directory:
            path = Path(directory) / "photo.png"
            _save_photo(photo, path)
            with _lock:
                results = _get_engine().predict(input=str(path))
                candidates = []
                for result in results:
                    text = " ".join(text.upper() if score >= MIN_CONFIDENCE else "|"
                                    for text, score in zip(result["rec_texts"], result["rec_scores"], strict=True))
                    candidates.extend(" ".join(match.split()) for match in ROOM_NUMBER.findall(text))
                return list(dict.fromkeys(candidates))
    except InvalidPhoto:
        raise
    except Exception as exc:
        raise OCRUnavailable("Photo recognition is unavailable. Please try again later.") from exc
