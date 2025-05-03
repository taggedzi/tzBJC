import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from tzBJC.gui import MainWindow

def test_encode_input_file_not_exist(monkeypatch, qtbot):
    main = MainWindow()
    qtbot.addWidget(main)

    qtbot.mouseClick(main.encode_button, Qt.LeftButton)
    window = main.encode_window
    qtbot.waitExposed(window)

    # Set non-existent input file
    bad_path = os.path.join(os.getcwd(), "no_such_file.bin")
    window.input_picker.set_path(bad_path)

    # Patch QMessageBox to avoid dialog blocking
    called = {}

    def fake_critical(*args, **kwargs):
        called['critical'] = True

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)

    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert called.get('critical') is True
