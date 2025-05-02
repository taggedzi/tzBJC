import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel

class ConverterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Binary <-> JSON Converter")
        layout = QVBoxLayout()

        self.label = QLabel("Choose an action.")
        layout.addWidget(self.label)

        self.button_to_json = QPushButton("Convert Binary to JSON")
        self.button_to_json.clicked.connect(self.convert_to_json)
        layout.addWidget(self.button_to_json)

        self.button_to_bin = QPushButton("Convert JSON to Binary")
        self.button_to_bin.clicked.connect(self.convert_to_binary)
        layout.addWidget(self.button_to_bin)

        self.setLayout(layout)

    def convert_to_json(self):
        input_file, _ = QFileDialog.getOpenFileName(self, "Open Binary File")
        output_file, _ = QFileDialog.getSaveFileName(self, "Save JSON File")
        if input_file and output_file:
            from .core import binary_to_signed_json
            with open(input_file, "rb") as f:
                data = f.read()
            json_str = binary_to_signed_json(data)
            with open(output_file, "w") as f:
                f.write(json_str)
            self.label.setText("Converted to JSON!")

    def convert_to_binary(self):
        input_file, _ = QFileDialog.getOpenFileName(self, "Open JSON File")
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Binary File")
        if input_file and output_file:
            from .core import signed_json_to_binary
            with open(input_file, "r") as f:
                json_str = f.read()
            binary = signed_json_to_binary(json_str)
            with open(output_file, "wb") as f:
                f.write(binary)
            self.label.setText("Converted to Binary!")

def main():
    app = QApplication(sys.argv)
    window = ConverterGUI()
    window.show()
    sys.exit(app.exec())
