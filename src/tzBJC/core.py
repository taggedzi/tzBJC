# Path: src/tzBJC/core.py
"""Library for encoding/decoding binary files to/from signed JSON files."""
# pylint: disable=line-too-long
import io
from io import TextIOBase
import hashlib
import base64
import os
import json
import re
from typing import TextIO
import zstandard as zstd


def encode_to_json_stream(input_path: str, output: TextIOBase, chunk_size: int = 65536) -> None:
    """
    Stream-compress a binary file, base64-encode it, and output a JSON object to a TextIO stream.
    The JSON includes filename, SHA256 checksum, and base64-encoded compressed data.

    :param input_path: Path to the input binary file.
    :param output: A text stream (e.g., sys.stdout, StringIO, or open(..., 'w')) to write the JSON to.
    :param chunk_size: Size of chunks to process in bytes.
    """
    hasher = hashlib.sha256()
    filename = os.path.basename(input_path)

    # Write JSON header and start of data field
    output.write('{\n')
    output.write(f'  "filename": {json.dumps(filename)},\n')
    output.write('  "checksum": "')

    # First pass: compute checksum
    with open(input_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    output.write(hasher.hexdigest() + '",\n')
    output.write('  "data": "')

    # Second pass: compress + encode
    cctx = zstd.ZstdCompressor(level=22)
    with open(input_path, "rb") as f, cctx.stream_reader(f) as compressor:
        while chunk := compressor.read(chunk_size):
            encoded_chunk = base64.urlsafe_b64encode(chunk).decode('ascii')
            output.write(encoded_chunk)

    output.write('"\n}\n')

def decode_from_json_stream(json_input: TextIO, output_path: str, chunk_size: int = 65536) -> None:
    """
    Reads a streamed JSON input containing compressed, base64-encoded binary data and writes
    the decompressed original binary file to output_path.

    :param json_input: A text stream containing the JSON structure.
    :param output_path: The path to write the decoded binary file.
    :param chunk_size: Size of chunks to decode and decompress.
    """
    # Parse the JSON and extract the base64 data
    json_obj = json.load(json_input)
    b64_data = json_obj["data"]

    # Decode the base64 into compressed bytes

    if not re.fullmatch(r'[-A-Za-z0-9_=]*', b64_data):
        raise ValueError("Invalid characters in base64 input")

    compressed_bytes = base64.urlsafe_b64decode(b64_data.encode("ascii"))

    # Decompress using zstandard
    dctx = zstd.ZstdDecompressor()
    with open(output_path, "wb") as out_file:
        with dctx.stream_reader(io.BytesIO(compressed_bytes)) as reader:
            while chunk := reader.read(chunk_size):
                out_file.write(chunk)
