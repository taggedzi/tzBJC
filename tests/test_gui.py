import os
import tempfile
import pytest
from PySide6.QtWidgets import QApplication
from tzBJC.gui import EncodeWindow, DecodeWindow

@pytest.fixture
def dummy_file():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
        tmp.write(b"dummy content")
        yield tmp.name
    os.remove(tmp.name)

def test_encode_autofill_output_path(qtbot, dummy_file):
    window = EncodeWindow()
    qtbot.addWidget(window)
    window.input_picker.set_path(dummy_file)

    expected = os.path.splitext(dummy_file)[0] + ".json"
    assert window.output_picker.path() == expected

def test_decode_autofill_output_path(qtbot):
    dummy_json = {
        "filename": "output.bin",
        "checksum": "123456",
        "data": "U29tZUJhc2U2NERhdGE="
    }
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tmp:
        import json
        json.dump(dummy_json, tmp)
        json_path = tmp.name

    window = DecodeWindow()
    qtbot.addWidget(window)
    window.input_picker.set_path(json_path)

    expected = os.path.join(os.path.dirname(json_path), "output.bin")
    assert window.output_picker.path() == expected

    os.remove(json_path)
