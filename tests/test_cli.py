# Path: tests/test_cli.py
# pylint: disable=line-too-long
"""Tests for the CLI."""
from io import StringIO
import json
import os
import sys
import tempfile
import pytest
from tzBJC.cli import main
from tzBJC.core import decode_from_json_stream


def test_cli_encode_decode_roundtrip(monkeypatch):
    """Test encoding and decoding a roundtrip."""
    original_data = b"CLI test data"

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.bin")
        json_path = os.path.join(tmpdir, "output.json")
        output_path = os.path.join(tmpdir, "restored.bin")

        # Write binary input file
        with open(input_path, "wb") as f:
            f.write(original_data)

        # Simulate: tzbjc-cli encode --input input.bin --output output.json
        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "encode", "--input", input_path, "--output", json_path])
        main()

        # Simulate: tzbjc-cli decode --input output.json --output restored.bin --force
        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "decode", "--input", json_path, "--output", output_path, "--force"])
        main()

        # Check that the output file matches the original
        with open(output_path, "rb") as f:
            result_data = f.read()

        assert result_data == original_data


def test_encode_streams_to_stdout(monkeypatch, capsys):
    """Test encoding streams to stdout."""
    data = b"streamed to stdout"

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.bin")
        restored_path = os.path.join(tmpdir, "restored.bin")

        with open(input_path, "wb") as f:
            f.write(data)

        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "encode", "--input", input_path])
        main()

        out = capsys.readouterr().out
        parsed = json.loads(out)

        assert "data" in parsed
        assert "checksum" in parsed
        assert "filename" in parsed

        # Decode from captured output
        json_stream = StringIO(out)
        decode_from_json_stream(json_stream, restored_path)

        with open(restored_path, "rb") as f:
            restored = f.read()

        assert restored == data


def test_decode_missing_output_and_json_filename(monkeypatch):
    """Test decoding when no output file is specified and no filename in JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_json_path = os.path.join(tmpdir, "bad.json")

        with open(bad_json_path, "w", encoding="utf-8") as f:
            f.write('{"checksum": "abc123", "data": "Zm9vYmFy"}')  # no filename

        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "decode", "--input", bad_json_path])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0


def test_encode_missing_input(monkeypatch):
    """Test encoding when no input file is specified."""
    fake_input = "no_such_file.bin"
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.json")
        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "encode", "--input", fake_input, "--output", output_path])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0


def test_encode_output_exists_without_force(monkeypatch):
    """Test encoding when the output file already exists without --force flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.bin")
        output_path = os.path.join(tmpdir, "output.json")

        with open(input_path, "wb") as f:
            f.write(b"test data")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("existing")

        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "encode", "--input", input_path, "--output", output_path])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

def test_decode_missing_data_field(monkeypatch):
    """Test decoding when the JSON file does not contain a 'data' field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "bad.json")
        output_path = os.path.join(tmpdir, "restored.bin")

        with open(json_path, "w", encoding="utf-8") as f:
            f.write('{"filename": "some.bin", "checksum": "abc123"}')  # no 'data'

        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "decode", "--input", json_path, "--output", output_path])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

def test_decode_invalid_base64(monkeypatch):
    """Test decoding when the JSON file contains an invalid base64 string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "bad.json")
        output_path = os.path.join(tmpdir, "restored.bin")

        with open(json_path, "w", encoding="utf-8") as f:
            f.write('{"filename": "some.bin", "checksum": "abc123", "data": "!@#$$%^^&"}')

        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "decode", "--input", json_path, "--output", output_path])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

def test_decode_output_exists_without_force(monkeypatch):
    """Test decoding when the output file already exists without --force flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.bin")
        json_path = os.path.join(tmpdir, "encoded.json")
        output_path = os.path.join(tmpdir, "restored.bin")

        # Setup: create binary -> encode -> try decode w/o force
        with open(input_path, "wb") as f:
            f.write(b"roundtrip")

        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "encode", "--input", input_path, "--output", json_path])
        main()

        with open(output_path, "wb") as f:
            f.write(b"existing")

        monkeypatch.setattr(sys, "argv", ["tzbjc-cli", "decode", "--input", json_path, "--output", output_path])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0
