import os
import tempfile
import pytest
from PySide6.QtCore import Qt
from tzBJC.gui import MainWindow

@pytest.fixture
def binary_file():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"dummy for toggle")
        yield f.name
    os.remove(f.name)

def test_toggle_output_mode_behavior(qtbot, binary_file):
    main = MainWindow()
    qtbot.addWidget(main)

    qtbot.mouseClick(main.encode_button, Qt.LeftButton)
    window = main.encode_window
    qtbot.waitExposed(window)

    # Set the input file
    window.input_picker.set_path(binary_file)

    # ✅ Initially output_checkbox is checked (file mode)
    assert window.output_checkbox.isChecked()
    assert window.output_picker.path_field.isEnabled()
    assert window.output_picker.browse_button.isEnabled()
    assert not window.text_output.isVisible()
    assert not window.copy_button.isVisible()

    # 🔁 Switch to text mode
    window.output_checkbox.setChecked(False)
    assert not window.output_picker.path_field.isEnabled()
    assert not window.output_picker.browse_button.isEnabled()
    assert window.text_output.isVisible()
    assert window.copy_button.isVisible()

    # 🔁 Switch back to file mode
    window.output_checkbox.setChecked(True)
    assert window.output_picker.path_field.isEnabled()
    assert window.output_picker.browse_button.isEnabled()
    assert not window.text_output.isVisible()
    assert not window.copy_button.isVisible()
