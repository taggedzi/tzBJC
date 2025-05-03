import os
import tempfile
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from tzBJC.gui import MainWindow

@pytest.fixture
def binary_file():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"clipboard test data")
        yield f.name
    os.remove(f.name)

def test_encode_to_text_and_clipboard(qtbot, binary_file):
    main = MainWindow()
    qtbot.addWidget(main)

    # Open encode window
    qtbot.mouseClick(main.encode_button, Qt.LeftButton)
    window = main.encode_window
    qtbot.waitExposed(window)

    # Set file and toggle output to text
    window.input_picker.set_path(binary_file)
    window.output_checkbox.setChecked(False)
    qtbot.mouseClick(window.convert_button, Qt.LeftButton)

    # Verify text output appears
    output = window.text_output.toPlainText()
    assert "filename" in output and "checksum" in output and "data" in output

    # Click copy and check clipboard
    qtbot.mouseClick(window.copy_button, Qt.LeftButton)
    clipboard = QApplication.clipboard()
    assert clipboard.text() == output
