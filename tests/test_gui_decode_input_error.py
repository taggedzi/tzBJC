import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from tzBJC.gui import MainWindow

def test_decode_input_file_not_exist(monkeypatch, qtbot):
    main = MainWindow()
    qtbot.addWidget(main)

    qtbot.mouseClick(main.decode_button, Qt.LeftButton)
    window = main.decode_window
    qtbot.waitExposed(window)

    # Set non-existent input JSON path
    bad_path = os.path.join(os.getcwd(), "no_such_file.json")
    window.input_picker.set_path(bad_path)

    # Prevent dialog blocking and track call
    called = {}

    def fake_critical(*args, **kwargs):
        called['critical'] = True

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)

    qtbot.mouseClick(window.convert_button, Qt.LeftButton)
    assert called.get('critical') is True
