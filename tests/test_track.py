from track import validate_G_record
import requests


class MockResponsePASS:
    # mock json() method always returns a specific testing dictionary
    @staticmethod
    def json():
        return {"result": "PASSED", "status": "IGC_PASSED", "msg": "vali-xcs.exe", "igc":"test_G_record_PASS.igc",
                "ref": "", "server": "Open Validation Server 3.03"}


class MockResponseFAIL:
    # mock json() method always returns a specific testing dictionary
    @staticmethod
    def json():
        return {"result": "FAILED", "status": "IGC_FAILED_NC", "msg": "vali-xcs.exe", "igc": "test_G_record_FAIL.igc",
                "ref": "", "server": "Open Validation Server 3.03"}


def test_validate_G_record_pass(monkeypatch):
    def mock_post(*args, **kwargs):
        return MockResponsePASS()

    monkeypatch.setattr(requests, "post", mock_post)

    result = validate_G_record('/app/tests/data/test_G_record_PASS.igc')
    assert result == "PASSED"


def test_validate_G_record_fail(monkeypatch):
    def mock_post(*args, **kwargs):
        return MockResponseFAIL()

    monkeypatch.setattr(requests, "post", mock_post)

    result = validate_G_record('/app/tests/data/test_G_record_FAIL.igc')
    assert result == "FAILED"


def test_validate_G_record_error(monkeypatch):
    def mock_post(*args, **kwargs):
        return MockResponseFAIL()

    monkeypatch.setattr(requests, "post", mock_post)

    result = validate_G_record('/app/tests/data/non_existant.igc')
    assert result == "ERROR"
