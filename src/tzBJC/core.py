# Path: src/tzBJC/core.py
"""
Encode any file into a JSON “package”:
  - compress with zlib (max compression)
  - URL-safe base64 (no padding)
  - wrap metadata (filename, checksum)

Decode a JSON package back to the original file.
"""
import io
import os
import sys
import argparse
import json
import zlib
import base64
import hashlib
import textwrap
import zstandard as zstd


def compute_checksum(data: bytes) -> str:
    """Return SHA-256 checksum of data as a hex string."""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def compress_data(data: bytes, compression_level: int = 22) -> bytes:
    """Compress data with zlib."""
    cctx = zstd.ZstdCompressor(level=compression_level)
    compressed = cctx.compress(data)
    return compressed


def binary_to_signed_json(in_path: str, compress_level: int = 22) -> None:
    # Read entire file
    with open(in_path, 'rb') as f:
        raw = f.read()

    checksum = compute_checksum(raw)
    
    cctx = zstd.ZstdCompressor(level=compress_level)
    compressed = cctx.compress(raw)
    
    b64 = base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')

    # Build minimal JSON object
    package = {
        "filename": os.path.basename(in_path),
        "checksum":  checksum,
        "data": b64,
    }

    return package


def decode_file(in_path: str) -> None:
    # Load JSON
    with open(in_path, 'r', encoding='utf-8') as f:
        pkg = json.load(f)

    fname = pkg["filename"]
    checksum_expected = pkg["checksum"]
    b64 = pkg["data"]

    # Restore padding for base64
    padding = (-len(b64)) % 4
    if padding:
        b64 += '=' * padding

    compressed = base64.urlsafe_b64decode(b64.encode('ascii'))
    dctx = zstd.ZstdDecompressor()
    raw = dctx.decompress(compressed)
    
    # Verify checksum
    checksum_actual = compute_checksum(raw)
    if checksum_actual != checksum_expected:
        print(f"Warning: checksum mismatch:\n"
              f"   expected: {checksum_expected}\n"
              f"     actual: {checksum_actual}",
              file=sys.stderr)

    return raw

def main():
    parser = argparse.ArgumentParser(
        prog='filepack.py',
        description='Compress any file to a zlib->URL-safe-base64 JSON package, or decode it back.',
        epilog=textwrap.dedent('''\
            Examples:
              # Encode a file:
              python filepack.py encode path/to/input.bin
              
              # Specify output JSON name:
              python filepack.py encode path/to/logo.png logo.pkg.json
              
              # Decode back into the original file (into cwd):
              python filepack.py decode logo.pkg.json
              
              # Decode into a specific folder:
              python filepack.py decode logo.pkg.json restored_folder/
        '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subs = parser.add_subparsers(dest='cmd', required=True, help='Available commands')

    enc = subs.add_parser(
        'encode',
        help='Compress & encode -> JSON package',
        description='Read INPUT, compress with zlib, base64-encode, wrap in JSON.'
    )
    enc.add_argument('input', help='Path to file to encode')
    enc.add_argument(
        'output',
        nargs='?',
        help='Output JSON filename (default: INPUT.json)'
    )

    dec = subs.add_parser(
        'decode',
        help='Decode JSON package -> original file',
        description='Read JSON package, base64-decode, decompress, verify checksum.'
    )
    dec.add_argument('input', help='Path to JSON package to decode')
    dec.add_argument(
        'output_dir',
        nargs='?',
        default='.',
        help='Directory to write the restored file (default: current directory)'
    )

    args = parser.parse_args()

    if args.cmd == 'encode':
        out = args.output or f"{args.input}.json"
        encode_file(args.input, out)
    else:  # decode
        decode_file(args.input, args.output_dir)


if __name__ == '__main__':
    main()



def binary_to_signed_json(binary_data: bytes) -> str:
    return json.dumps({"data": list(binary_data)})

def signed_json_to_binary(json_str: str) -> bytes:
    obj = json.loads(json_str)
    return bytes(obj["data"])
