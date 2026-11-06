from io import BytesIO
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from utils import ocr


@pytest.fixture(params=["PNG", "JPEG"])
def photo(request):
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (80, 40), "white").save(buffer, format=request.param)
    return buffer.getvalue()


@pytest.fixture
def engine(monkeypatch):
    state = SimpleNamespace(results=[], paths=[])

    def predict(*, input):
        assert Path(input).is_file()
        state.paths.append(Path(input))
        yield from state.results

    monkeypatch.setattr(ocr, "_get_engine", lambda: SimpleNamespace(predict=predict))
    return state


@pytest.mark.parametrize("building", ["UNC", "FIP", "COM", "ASC", "ART", "CCS", "ADM", "SCI", "LIB"])
def test_extracts_distinct_room_numbers_above_confidence_threshold(photo, engine, building):
    engine.results = [{"rec_texts": [f"Office {building} 308", "EME 0050", "sci  001", "ART", "123", "SCI 999"],
                       "rec_scores": [0.99, 0.95, 0.8, 0.9, 0.9, 0.79]},
                      {"rec_texts": ["LIB", "308", "ART", "999", "eme", "0050"],
                       "rec_scores": [0.79, 0.99, 0.99, 0.79, 0.99, 0.99]}]
    assert ocr.extract_room_numbers(photo) == [f"{building} 308", "EME 0050", "SCI 001", "ART 123"]
    assert all(not path.exists() for path in engine.paths)


def test_engine_is_initialized_lazily_and_reused(monkeypatch):
    calls = []
    engine = object()

    def create(**options):
        calls.append(options)
        return engine

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=create))
    ocr._get_engine.cache_clear()
    try:
        assert ocr._get_engine() is ocr._get_engine() is engine
        assert len(calls) == 1
        assert calls[0]["device"] == "cpu"
    finally:
        ocr._get_engine.cache_clear()


def test_unsupported_image_format_is_rejected(engine):
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, format="GIF")
    with pytest.raises(ocr.InvalidPhoto, match="JPEG or PNG"):
        ocr.extract_room_numbers(buffer.getvalue())
    assert engine.paths == []


@pytest.mark.parametrize("text,score", [("Faculty office", 0.99), ("308", 0.99), ("LIB", 0.99), ("XYZ 308", 0.99),
    ("LIB308", 0.99), ("LI 308", 0.99), ("LIB 30", 0.99), ("LIB 3081", 0.99), ("EME 050", 0.99),
    ("LIB 308A", 0.99), ("XLIB 308", 0.99), ("LIB-308", 0.99), ("LIB 308", 0.79), ("EME 00500", 0.99)])
def test_unreadable_or_non_number_text_returns_no_candidates(photo, engine, text, score):
    engine.results = [{"rec_texts": [text], "rec_scores": [score]}]
    assert ocr.extract_room_numbers(photo) == []


def test_no_detections_returns_no_candidates(photo, engine):
    assert ocr.extract_room_numbers(photo) == []


@pytest.mark.parametrize("invalid", [b"", b"not an image", None, b"x" * (ocr.MAX_PHOTO_BYTES + 1)])
def test_invalid_photo_never_calls_engine(invalid, engine):
    with pytest.raises(ocr.InvalidPhoto):
        ocr.extract_room_numbers(invalid)
    assert engine.paths == []


def test_pixel_limit_rejects_photo_before_inference(photo, engine, monkeypatch):
    monkeypatch.setattr(ocr, "MAX_PHOTO_PIXELS", 1)
    with pytest.raises(ocr.InvalidPhoto):
        ocr.extract_room_numbers(photo)
    assert engine.paths == []


@pytest.mark.parametrize("error", [ImportError("private runtime details"), RuntimeError("private model details")])
def test_engine_failure_has_friendly_error_and_cleans_up(photo, engine, monkeypatch, error):
    def fail(*, input):
        engine.paths.append(Path(input))
        raise error

    monkeypatch.setattr(ocr, "_get_engine", lambda: SimpleNamespace(predict=fail))
    with pytest.raises(ocr.OCRUnavailable, match="Photo recognition is unavailable") as caught:
        ocr.extract_room_numbers(photo)
    assert "private" not in str(caught.value)
    assert all(not path.exists() for path in engine.paths)
