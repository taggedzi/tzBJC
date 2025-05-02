import os
import tempfile
from io import StringIO
from tzBJC.core import encode_to_json_stream, decode_from_json_stream

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
