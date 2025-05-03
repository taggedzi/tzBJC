# tzBJC - TaggedZ's Binary to JSON Converter

**tzBJC** is a utility for encoding and decoding binary files to signed JSON format with Zstandard compression. It provides both a command-line interface (CLI) and a graphical user interface (GUI) built with PySide6.

---

## ✨ Features

- 🔐 Encodes binary files into signed JSON format
- 🔌 Library for easy integration into other projects
- 🧩 Uses Zstandard compression with Base64 URL-safe encoding
- 📦 CLI and GUI support
- ✅ Stream-based processing for large files
- 📋 Clipboard-friendly JSON output (via GUI)
- 🧪 Thorough test coverage with Pytest and Pytest-Qt

---

## 📦 Installation

```bash
pip install tzBJC
```

Or from source:

```bash
git clone https://github.com/taggedzi/tzBJC.git
cd tzBJC
pip install .
```

---

## 🖥️ Command Line Usage

See CLI help:

```bash
tzBJC-cli --help
```

### Encode example:

```bash
tzBJC-cli encode -i input.bin -o output.json
```

### Decode example:

```bash
tzBJC-cli decode -i output.json -o restored.bin
```

---

## 🪟 GUI Usage

```bash
tzBJC-gui
```

Drag-and-drop or select binary or JSON files to convert between formats. The GUI supports:

- File output
- Clipboard-friendly output
- Overwrite protection (with `force` option)

---

## 🛠 Developer Instructions

Set up a local development environment:

```bash
git clone https://github.com/taggedzi/tzBJC.git
cd tzBJC
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -e .[dev]
```

Run tests with coverage:

```bash
pytest --cov=src
```

Build the package:

```bash
python -m build
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌐 Links

- 📦 [PyPI Project Page](https://pypi.org/project/tzBJC/)
- 🐙 [GitHub Repository](https://github.com/taggedzi/tzBJC)
- 🗃️ [Project README](README.md)
- 📖 [Documentation](https://taggedzi.github.io/tzBJC/)
