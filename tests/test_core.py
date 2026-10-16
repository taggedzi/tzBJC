import base64
import json
import pytest
import os
import random
import tempfile
import zstandard as zstd
from io import StringIO
from tzBJC.core import encode_to_json_stream, decode_from_json_stream


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 7, 65536])
def test_multichunk_base64_roundtrip(tmp_path, chunk_size):
    """The payload must be one valid Base64 string across chunk boundaries."""
    rng = random.Random(42)
    original = bytes(rng.getrandbits(8) for _ in range(200000))
    input_path = tmp_path / "input.bin"
    output_path = tmp_path / "restored.bin"
    input_path.write_bytes(original)

    stream = StringIO()
    encode_to_json_stream(str(input_path), stream, chunk_size=chunk_size)
    payload = json.loads(stream.getvalue())["data"]
    # Strict decoding also detects embedded padding, beyond checking our own decoder.
    compressed = base64.b64decode(payload, altchars=b"-_", validate=True)
    with zstd.ZstdDecompressor().stream_reader(compressed) as reader:
        assert reader.read() == original

    stream.seek(0)
    decode_from_json_stream(stream, str(output_path))
    assert output_path.read_bytes() == original

def test_roundtrip_encoding_decoding():
    original_data = b"this is some test binary data for zstandard compression roundtrip."
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.bin")
        output_path = os.path.join(tmpdir, "output.bin")

        with open(input_path, "wb") as f:
            f.write(original_data)

        # Encode to JSON in memory
        json_buffer = StringIO()
        encode_to_json_stream(input_path, json_buffer)
        json_buffer.seek(0)

        # Decode from JSON
        decode_from_json_stream(json_buffer, output_path)

        # Validate output
        with open(output_path, "rb") as f:
            result = f.read()

        assert result == original_data

def test_decode_checksum_mismatch(tmp_path):
    # Compress known data using Zstandard
    original_data = b"hello world"
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(original_data)

    # Encode compressed data in base64-url-safe
    b64_data = base64.urlsafe_b64encode(compressed).decode("ascii")

    # Craft JSON with intentionally incorrect checksum
    fake_json = {
        "filename": "test.bin",
        "checksum": "deadbeef" * 8,
        "data": b64_data
    }

    json_input = StringIO(json.dumps(fake_json))
    out_path = tmp_path / "output.bin"

    with pytest.raises(ValueError, match="Checksum mismatch"):
        decode_from_json_stream(json_input, str(out_path))
