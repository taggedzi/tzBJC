import os
import tempfile
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox
from tzBJC.gui import MainWindow

@pytest.fixture
def binary_file():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"binary content")
        yield f.name
    os.remove(f.name)

def test_encode_full_flow(qtbot, binary_file, monkeypatch):
    main = MainWindow()
    qtbot.addWidget(main)

    # Simulate clicking the encode button
    qtbot.mouseClick(main.encode_button, Qt.LeftButton)
    window = main.encode_window
    qtbot.waitExposed(window)

    # Set binary input
    window.input_picker.set_path(binary_file)
    output_path = os.path.splitext(binary_file)[0] + ".json"
    window.output_picker.set_path(output_path)

    # Convert to file with force (should succeed)
    window.force_checkbox.setChecked(True)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert os.path.exists(output_path)

    # Patch QMessageBox.warning to prevent blocking
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

    # Attempt overwrite without force (should not hang)
    window.force_checkbox.setChecked(False)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert os.path.exists(output_path)

    # Switch to text output
    window.output_checkbox.setChecked(False)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert "filename" in window.text_output.toPlainText()

    # Copy to clipboard
    qtbot.mouseClick(window.copy_button, Qt.LeftButton)
    clipboard = QApplication.clipboard()
    assert "filename" in clipboard.text()

    os.remove(output_path)
