import sys
import os
import json
from pathlib import Path
import base64
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QLabel, QLineEdit,
    QVBoxLayout, QHBoxLayout, QTextEdit, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from tzBJC.core import encode_to_json_stream, decode_from_json_stream
from io import StringIO

class FilePicker(QWidget):
    def __init__(self, label, file_mode):
        super().__init__()
        self.file_mode = file_mode
        layout = QHBoxLayout()
        self.label = QLabel(label)
        self.path_field = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.pick_file)
        layout.addWidget(self.label)
        layout.addWidget(self.path_field)
        layout.addWidget(self.browse_button)
        self.setLayout(layout)

    def pick_file(self):
        if self.file_mode == 'open':
            path, _ = QFileDialog.getOpenFileName(self, "Select file")
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Save file")
        if path:
            self.set_path(path)

    def path(self):
        return self.path_field.text()

    def set_path(self, path):
        normalized = Path(path).as_posix()
        self.path_field.setText(normalized)
        self.on_path_changed(path)

    def clear_path(self):
        self.path_field.clear()

    def set_enabled(self, enabled):
        self.path_field.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)

    def on_path_changed(self, path):
        pass  # Can be overridden by parent

class EncodeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convert Binary to JSON")
        self.resize(640, 240)
        layout = QVBoxLayout()

        self.input_picker = FilePicker("Binary Input:", 'open')
        self.input_picker.on_path_changed = self.autofill_output_path
        layout.addWidget(self.input_picker)

        checkbox_row = QHBoxLayout()
        self.output_checkbox = QCheckBox("Output to file")
        self.output_checkbox.setChecked(True)
        self.output_checkbox.stateChanged.connect(self.toggle_output_mode)
        checkbox_row.addWidget(self.output_checkbox)

        self.force_checkbox = QCheckBox("Force overwrite if file already exists.")
        checkbox_row.addWidget(self.force_checkbox)

        layout.addLayout(checkbox_row)

        self.output_picker = FilePicker("Output JSON File:", 'save')
        layout.addWidget(self.output_picker)
        self.output_picker.show()

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.hide()
        layout.addWidget(self.text_output)
        
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.hide()
        layout.addWidget(self.copy_button)

        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.convert)
        layout.addWidget(self.convert_button)

        self.setLayout(layout)

    def autofill_output_path(self, input_path):
        if os.path.isfile(input_path):
            base, _ = os.path.splitext(os.path.basename(input_path))
            directory = os.path.dirname(input_path)
            default_output = os.path.join(directory, f"{base}.json")
            self.output_picker.set_path(default_output)

    def toggle_output_mode(self):
        if self.output_checkbox.isChecked():
            self.output_picker.set_enabled(True)
            self.autofill_output_path(self.input_picker.path())
            self.text_output.hide()
            self.copy_button.hide()
        else:
            self.output_picker.clear_path()
            self.output_picker.set_enabled(False)
            self.text_output.show()
            self.copy_button.show()

    def convert(self):
        input_path = self.input_picker.path()
        if not os.path.exists(input_path):
            QMessageBox.critical(self, "Error", "Input file does not exist.")
            return

        if self.output_checkbox.isChecked():
            output_path = self.output_picker.path()
            if os.path.exists(output_path) and not self.force_checkbox.isChecked():
                QMessageBox.warning(self, "Warning", "Output file exists. Use force to overwrite.")
                return
            with open(output_path, "w", encoding="utf-8") as f:
                encode_to_json_stream(input_path, f)
        else:
            buffer = StringIO()
            encode_to_json_stream(input_path, buffer)
            buffer.seek(0)
            self.text_output.setPlainText(buffer.read())

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_output.toPlainText())

class DecodeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convert JSON to Binary")
        self.resize(640, 240)
        layout = QVBoxLayout()

        self.input_picker = FilePicker("JSON Input:", 'open')
        self.input_picker.on_path_changed = self.autofill_output_path
        layout.addWidget(self.input_picker)

        self.force_checkbox = QCheckBox("Force overwrite if file already exists.")
        layout.addWidget(self.force_checkbox)
        
        self.output_picker = FilePicker("Binary Output File:", 'save')
        layout.addWidget(self.output_picker)
        self.output_picker.show()

        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.convert)
        layout.addWidget(self.convert_button)

        self.setLayout(layout)

    def autofill_output_path(self, input_path):
        if os.path.isfile(input_path):
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    parsed = json.load(f)
                    filename = parsed.get("filename")
                    if filename:
                        directory = os.path.dirname(input_path)
                        default_output = os.path.join(directory, filename)
                        self.output_picker.set_path(default_output)
            except Exception:
                pass

    def convert(self):
        input_path = self.input_picker.path()
        if not os.path.exists(input_path):
            QMessageBox.critical(self, "Error", "Input JSON does not exist.")
            return

        with open(input_path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
            f.seek(0)
            output_path = self.output_picker.path()

            if not output_path:
                QMessageBox.critical(self, "Error", "No output file specified.")
                return

            if os.path.exists(output_path) and not self.force_checkbox.isChecked():
                QMessageBox.warning(self, "Warning", "Output file exists. Use force to overwrite.")
                return

            decode_from_json_stream(StringIO(json.dumps(parsed)), output_path)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("tzBJC - TaggedZ's Binary JSON Converter")
        self.resize(480, 320)
        layout = QVBoxLayout()

        self.instruction_label = QLabel("\u2193 Drag and drop a file here to auto-detect format and open the correct converter \u2193")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.instruction_label)

        self.encode_button = QPushButton("Convert Binary to JSON")
        self.encode_button.clicked.connect(self.open_encode_window)
        layout.addWidget(self.encode_button)

        self.decode_button = QPushButton("Convert JSON to Binary")
        self.decode_button.clicked.connect(self.open_decode_window)
        layout.addWidget(self.decode_button)

        self.setLayout(layout)
        self.setAcceptDrops(True)

    def open_encode_window(self, path=None):
        self.encode_window = EncodeWindow()
        if path:
            self.encode_window.input_picker.set_path(path)
        self.encode_window.show()

    def open_decode_window(self, path=None):
        self.decode_window = DecodeWindow()
        if path:
            self.decode_window.input_picker.set_path(path)
        self.decode_window.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if not os.path.isfile(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)
            self.open_decode_window(path)
        except Exception:
            self.open_encode_window(path)

def main():
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
