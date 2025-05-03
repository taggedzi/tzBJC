import os
import tempfile
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from tzBJC.gui import MainWindow

@pytest.fixture
def encoded_json_file():
    data = {
        "filename": "restored_output.bin",
        "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "data": "KLUv_QA="
    }
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        import json
        json.dump(data, f)
        return f.name

def test_decode_flow_with_force(monkeypatch, qtbot, encoded_json_file):
    main = MainWindow()
    qtbot.addWidget(main)

    # Open decode window and set file path
    qtbot.mouseClick(main.decode_button, Qt.LeftButton)
    window = main.decode_window
    qtbot.waitExposed(window)

    window.input_picker.set_path(encoded_json_file)
    output_path = os.path.join(os.path.dirname(encoded_json_file), "restored_output.bin")
    window.output_picker.set_path(output_path)

    # First conversion with force
    window.force_checkbox.setChecked(True)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert os.path.exists(output_path)

    # Patch QMessageBox.warning to avoid blocking
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

    # Second conversion without force (should skip overwrite)
    window.force_checkbox.setChecked(False)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert os.path.exists(output_path)

    os.remove(output_path)
    os.remove(encoded_json_file)
