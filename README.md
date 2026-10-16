# tzBJC

### TaggedZ's Binary JSON Converter

**Turn a binary file into portable JSON, then restore the original bytes.**

[![CI](https://github.com/taggedzi/tzBJC/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/taggedzi/tzBJC/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tzBJC?logo=pypi&logoColor=white)](https://pypi.org/project/tzBJC/)
[![Python](https://img.shields.io/badge/python-3.9%E2%80%933.13-3776AB?logo=python&logoColor=white)](#installation)
[![Status](https://img.shields.io/badge/status-beta-F59E0B)](https://github.com/taggedzi/tzBJC)
[![License: MIT](https://img.shields.io/badge/license-MIT-10B981)](https://github.com/taggedzi/tzBJC/blob/main/LICENSE)

tzBJC packages one file into a JSON object containing its filename, a SHA-256
checksum, and its Zstandard-compressed contents encoded as URL-safe Base64.
Use it from the command line, a desktop app, or your own Python code.

It is useful when a system accepts text or JSON but you need to carry binary
content: an attachment in a JSON payload, a test fixture, or a file you want to
copy through a text-only interface. The decoder verifies the checksum before
writing the restored file.

**The checksum detects corruption. It is not a digital signature, proof of
authorship, or encryption.** Anyone who can replace the contents can also replace
the checksum.

[Install](#installation) · [CLI](#command-line-usage) · [Desktop app](#desktop-app) ·
[Python API](#python-api) · [Development](#development) · [Releasing](#releasing)

## How it works

![Encoding: calculate SHA-256 and compress then Base64-encode the original file into JSON. Decoding: decode, decompress, and verify the checksum before writing the restored file.](https://raw.githubusercontent.com/taggedzi/tzBJC/main/docs/assets/conversion-flow.svg)

[View the SVG diagram](https://github.com/taggedzi/tzBJC/blob/main/docs/assets/conversion-flow.svg)

Each JSON document represents **one file**, with these fields:

| Field | Contents |
| --- | --- |
| `filename` | Original file's basename, without its directory |
| `checksum` | SHA-256 of the original, uncompressed bytes, as hexadecimal text |
| `data` | URL-safe Base64 text containing the Zstandard-compressed bytes |

Compression can reduce the file size, but JSON output is not guaranteed to be
smaller. Base64 adds roughly one-third to the compressed size, and already
compressed formats such as ZIP or JPEG may not shrink much.

## Installation

Use **Python 3.9–3.13** on a platform supported by
[PySide6 6.9.0](https://pypi.org/project/PySide6/6.9.0/).
Python 3.10–3.13 is required for development and tests.
The package installs Qt/PySide6 even when you only use the CLI or library.

Create a virtual environment:

```sh
python -m venv .venv
```

Activate it using the command for your shell:

| Shell | Command |
| --- | --- |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| macOS / Linux (bash or zsh) | `source .venv/bin/activate` |

Then install the latest published release:

```sh
python -m pip install --upgrade pip
python -m pip install tzBJC
```

To install the code from a checkout instead, run `python -m pip install .` in
the repository root. The PyPI badge above shows the **published** version;
the checkout may contain changes that have not been released yet.

## Command-line usage

Encode a file and restore it to a new path:

```sh
tzBJC-cli encode -i input.bin -o encoded.json
tzBJC-cli decode -i encoded.json -o restored.bin
```

The restored file contains the same bytes as `input.bin`. Both commands refuse
to overwrite an existing output file unless you add `--force` (or `-f`).
Quote paths containing spaces.

| Task | Command |
| --- | --- |
| Show help | `tzBJC-cli --help` |
| Show encode options | `tzBJC-cli encode --help` |
| Write JSON to standard output | `tzBJC-cli encode -i input.bin` |
| Restore using the embedded filename | `tzBJC-cli decode -i encoded.json` |
| Replace an existing output | `tzBJC-cli decode -i encoded.json -o restored.bin --force` |

When `-o` is omitted during decoding, the embedded filename determines the
output path; normally this writes to the current directory. For JSON received
from someone else, **specify your own output path with `-o`**: the decoder does
not sanitize the embedded filename. Input JSON must be a file; stdin is not
currently supported.

See the [CLI reference](https://github.com/taggedzi/tzBJC/blob/main/CLI.md)
for all options and exit codes.

## Desktop app

```sh
tzBJC-gui
```

1. Choose **Convert Binary to JSON** or **Convert JSON to Binary**, then browse
   for an input file and check the output path. You can also drop a file onto
   the main window to open a converter automatically.
2. Click **Convert**. When encoding, clear **Output to file** to display the
   JSON as text, then use **Copy to Clipboard**.

Existing files are protected unless you select **Force overwrite if file
already exists**. Drag-and-drop treats parseable JSON as decode input; use the
explicit encode button to package an ordinary JSON file. Decoding requires a
tzBJC document, not arbitrary JSON. The GUI needs a graphical desktop session.

## Python API

The library takes an input path and a writable text stream for encoding,
or a readable JSON text stream and an output path for decoding:

```python
from tzBJC.core import encode_to_json_stream, decode_from_json_stream

with open("encoded.json", "w", encoding="utf-8") as output:
    encode_to_json_stream("input.bin", output)

with open("encoded.json", "r", encoding="utf-8") as source:
    decode_from_json_stream(source, "restored.bin")
```

Use `io.StringIO` instead of a file to work with JSON in memory. A checksum
mismatch raises `ValueError` and prevents the decoded output from being written.
Unlike the CLI and GUI, the library **overwrites an existing output path**;
check for an existing file yourself when that matters.

## Current limits

- Encoding reads the input twice: once to hash it, then to compress it. Keep the
  input unchanged during conversion. Zstandard uses compression level 22, which
  favors compression over speed and can use substantial memory.
- Decoding loads the JSON, compressed payload, and restored bytes into memory.
  The stream-based function names do not imply bounded-memory decoding. Choose
  input sizes that fit your available RAM; there is no decompressed-size limit.
- There is no password protection, encryption, multi-file archive support, or
  authenticity check. Process JSON from trusted sources.
- Releases before 0.2.18 can produce invalid Base64 across compression chunks.
  If an older document fails verification, re-encode the original with 0.2.18
  or newer. Updating the decoder alone does not repair an old document.

## Development

Clone the repository:

```sh
git clone https://github.com/taggedzi/tzBJC.git
cd tzBJC
```

Create and activate a virtual environment as above, then install the development
packages and run the tests:

```sh
python -m pip install -e ".[dev]"
python -m pytest --cov=tzBJC --cov-report=term-missing
```

GUI tests use pytest-qt. For headless runs, set `QT_QPA_PLATFORM=offscreen` before
running pytest (`$env:QT_QPA_PLATFORM="offscreen"` in PowerShell or
`export QT_QPA_PLATFORM=offscreen` in bash). Linux also needs the Qt system
libraries; see the [CI workflow](https://github.com/taggedzi/tzBJC/blob/main/.github/workflows/ci.yml)
for the Ubuntu setup used by this project. CI currently runs on Python 3.10
and Ubuntu, rather than testing every supported Python/platform combination.

To build a wheel and source distribution:

```sh
python -m pip install build
python -m build
```

Artifacts are written to `dist/`.

## Releasing

Version **0.2.18** is a patch release for maintenance and the Base64 chunk fix.
See the [changelog](https://github.com/taggedzi/tzBJC/blob/main/CHANGELOG.md) for details.

Use Invoke to prepare both version files and validate the release:

```sh
python -m invoke prepare-release --version=0.2.18
python -m invoke release --version=0.2.18
```

After reviewing, committing, and merging the changes to `main`, add `--publish`
to validate again and push the production release tag. Add `--test --publish`
for a TestPyPI-only trial. GitHub Actions handles uploads; the local task does
not upload packages. Follow the [release guide](https://github.com/taggedzi/tzBJC/blob/main/RELEASING.md)
for checks and exact commands before publishing.

## License and links

tzBJC is licensed under the [MIT License](https://github.com/taggedzi/tzBJC/blob/main/LICENSE).

[PyPI](https://pypi.org/project/tzBJC/) ·
[Source code](https://github.com/taggedzi/tzBJC) ·
[Issues](https://github.com/taggedzi/tzBJC/issues) ·
[Generated API docs](https://taggedzi.github.io/tzBJC/)

The checked-in API documentation is generated separately and may lag behind
the source code.
