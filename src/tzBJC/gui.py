# Path: src/tzBJC/core.py
"""The gui module contains the main application logic and user interface components."""
# pylint: disable=line-too-long
import json
import os
import sys
from pathlib import Path
from io import StringIO
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QLabel, QLineEdit,
    QVBoxLayout, QHBoxLayout, QTextEdit, QCheckBox, QMessageBox
)
from PySide6.QtGui import QClipboard  # noqa: F401
from tzBJC.core import encode_to_json_stream, decode_from_json_stream


class FilePicker(QWidget):
    """A widget for picking a file."""

    def __init__(self, label: str, file_mode: str):
        """Initialize a FilePicker widget.

        Args:
            label (str): The label for the file picker. 
            file_mode (str): the mode of the file picker, either "save" or "open".
        """
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
        """Open a file dialog to pick a file."""
        if self.file_mode == 'open':
            path, _ = QFileDialog.getOpenFileName(self, "Select file")
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Save file")
        if path:
            self.set_path(path)

    def path(self):
        """Get the current file path."""
        return self.path_field.text()

    def set_path(self, path):
        """Set the current file path. So it is displayed in POSIX format.
        
        Args:
            path (str): The file path.
        """
        normalized = Path(path).as_posix()
        self.path_field.setText(normalized)
        self.on_path_changed(path)

    def clear_path(self):
        """Clear the current file path."""
        self.path_field.clear()

    def set_enabled(self, enabled):
        """Set the enabled state of the file picker.
        
        Args:
            enabled (bool): True if the file picker should be enabled, False otherwise.
        """
        self.path_field.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)

    def on_path_changed(self, path):
        """Called when the path field changes. Can be overridden by subclasses."""


class EncodeWindow(QWidget):
    """The Encoder window for encoding binary files to JSON.

    Args:
        QWidget (QWidget): The parent widget for the window.
    """

    def __init__(self):
        """Initialize the EncodeWindow."""
        super().__init__()

        # Setup the window properties
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

    def autofill_output_path(self, input_path: str):
        """Autofill the output path based on the input file name.

        Args:
            input_path (str): The path to the input file.
        """
        if os.path.isfile(input_path):
            base, _ = os.path.splitext(os.path.basename(input_path))
            directory = os.path.dirname(input_path)
            default_output = os.path.join(directory, f"{base}.json")
            self.output_picker.set_path(default_output)

    def toggle_output_mode(self):
        """Toggle between text output and JSON file output."""
        if self.output_checkbox.isChecked():
            # Output JSON file
            self.output_picker.set_enabled(True)
            self.autofill_output_path(self.input_picker.path())
            self.text_output.hide()
            self.copy_button.hide()
        else:
            # Output text
            self.output_picker.clear_path()
            self.output_picker.set_enabled(False)
            self.text_output.show()
            self.copy_button.show()

    def convert(self):
        """Convert the input binary file to JSON."""
        input_path = self.input_picker.path()
        if not os.path.exists(input_path):
            QMessageBox.critical(self, "Error", "Input file does not exist.")
            return

        if self.output_checkbox.isChecked():
            # Output JSON file
            output_path = self.output_picker.path()

            if os.path.exists(output_path) and not self.force_checkbox.isChecked():
                QMessageBox.warning(self, "Warning", "Output file exists. Use force to overwrite.")
                return

            with open(output_path, "w", encoding="utf-8") as f:
                encode_to_json_stream(input_path, f)
        else:
            # Output text to text area
            buffer = StringIO()
            encode_to_json_stream(input_path, buffer)
            buffer.seek(0)
            self.text_output.setPlainText(buffer.read())

    def copy_to_clipboard(self):
        """Copy the output to the clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_output.toPlainText())


class DecodeWindow(QWidget):
    """Decode window for converting JSON to binary files.

    Args:
        QWidget (QWidget): The parent widget for the decode window.
    """

    def __init__(self):
        """Initialize the decode window."""

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

    def autofill_output_path(self, input_path: str):
        """Auto-fill the output path based on the input's path

        Args:
            input_path (str): the url of the file to be converted
        """
        if os.path.isfile(input_path):
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    parsed = json.load(f)
                    # Parse the filename from the JSON
                    filename = parsed.get("filename")
                    if filename:
                        directory = os.path.dirname(input_path)
                        default_output = os.path.join(directory, filename)
                        self.output_picker.set_path(default_output)
            except Exception:
                pass

    def convert(self):
        """Convert the input JSON to a binary file."""

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
    """Main window for the application.

    Args:
        QWidget (QWidget): Parent widget for the main window.
    """
    def __init__(self):
        """Initialize the main window."""

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

    def open_encode_window(self, path: str = None):
        """Open the encode window.

        Args:
            path (str, optional): The path of the file to encode. Defaults to None.
        """
        self.encode_window = EncodeWindow()
        if path:
            self.encode_window.input_picker.set_path(path)
        self.encode_window.show()

    def open_decode_window(self, path: str = None):
        """Open the decode window.

        Args:
            path (str, optional): The path to the file to decode. Defaults to None.
        """
        self.decode_window = DecodeWindow()
        if path:
            self.decode_window.input_picker.set_path(path)
        self.decode_window.show()

    def dragEnterEvent(self, event):
        """Process the drag enter event.

        Args:
            event (QDragEnterEvent): PySide6.QtCore.QDragEnterEvent): The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Process the drop event.

        Args:
            event (QDropEvent): PySide6.QtCore.QDropEvent. The drop event.
        """
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
    """The main function to run the application."""
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
