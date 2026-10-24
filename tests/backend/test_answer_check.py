from utils.answer_check import check_answer


def test_every_photo_counts_as_correct_until_ocr_and_gps_are_added():
    assert check_answer(b"any photo", {"room_number": "312"}) is True
