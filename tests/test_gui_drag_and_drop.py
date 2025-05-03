import os
import tempfile
import pytest
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent
from PySide6.QtWidgets import QApplication
from tzBJC.gui import MainWindow

@pytest.fixture
def json_file():
    data = {
        "filename": "output.bin",
        "checksum": "abc",
        "data": "U29tZUJhc2U2NERhdGE="
    }
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        import json as js
        js.dump(data, f)
        return f.name

@pytest.fixture
def binary_file():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"drag and drop test")
        return f.name

def simulate_drop(widget, file_path):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(file_path)])
    event = QDragEnterEvent(widget.pos(), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    widget.dragEnterEvent(event)
    drop_event = QDropEvent(widget.pos(), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    widget.dropEvent(drop_event)

def test_drag_drop_json_opens_decode(qtbot, json_file):
    main = MainWindow()
    qtbot.addWidget(main)
    main.show()
    simulate_drop(main, json_file)
    assert hasattr(main, 'decode_window')
    assert Path(main.decode_window.input_picker.path()).as_posix() == Path(json_file).as_posix()
    os.remove(json_file)

def test_drag_drop_bin_opens_encode(qtbot, binary_file):
    main = MainWindow()
    qtbot.addWidget(main)
    main.show()
    simulate_drop(main, binary_file)
    assert hasattr(main, 'encode_window')
    assert Path(main.encode_window.input_picker.path()).as_posix() == Path(binary_file).as_posix()
    os.remove(binary_file)
