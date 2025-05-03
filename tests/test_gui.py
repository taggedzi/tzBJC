import os
import tempfile
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from tzBJC.gui import MainWindow, EncodeWindow, DecodeWindow
from PySide6.QtCore import Qt


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
    assert Path(window.output_picker.path()).as_posix() == Path(expected).as_posix()

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
    assert Path(window.output_picker.path()).as_posix() == Path(expected).as_posix()

    os.remove(json_path)


@pytest.fixture
def binary_file():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"binary content")
        yield f.name
    os.remove(f.name)

def test_encode_force_behavior(qtbot, binary_file, monkeypatch):
    main = MainWindow()
    qtbot.addWidget(main)
    qtbot.mouseClick(main.encode_button, Qt.LeftButton)
    window = main.encode_window
    qtbot.waitExposed(window)

    # Setup input and output path
    window.input_picker.set_path(binary_file)
    output_path = os.path.splitext(binary_file)[0] + ".json"
    window.output_picker.set_path(output_path)

    # Force overwrite (creates file)
    window.force_checkbox.setChecked(True)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert os.path.exists(output_path)

    # 🔧 Patch the dialog to prevent blocking
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

    # Now test non-force overwrite (should not hang)
    window.force_checkbox.setChecked(False)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)

    # Still safe: file should exist
    assert os.path.exists(output_path)

    os.remove(output_path)
    
    
def test_encode_force_behavior_select_file(qtbot, binary_file, monkeypatch):
    main = MainWindow()
    qtbot.addWidget(main)
    qtbot.mouseClick(main.encode_button, Qt.LeftButton)
    window = main.encode_window
    qtbot.waitExposed(window)

    # Setup input and output path
    window.input_picker.set_path(binary_file)
    output_path = os.path.splitext(binary_file)[0] + ".json"
    window.output_picker.set_path(output_path)

    # Force overwrite (creates file)
    window.force_checkbox.setChecked(True)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert os.path.exists(output_path)

    # 🔧 Patch the dialog to prevent blocking
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

    # Now test non-force overwrite (should not hang)
    window.force_checkbox.setChecked(False)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)

    # Still safe: file should exist
    assert os.path.exists(output_path)

    os.remove(output_path)