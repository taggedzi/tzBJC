# Path: src/tzBJC/cli.py
"""CLI interface for tzBJC."""
# pylint: disable=line-too-long
import argparse
import binascii
import json
import os
import sys
from io import StringIO
import zstandard as zstd
from tzBJC.core import encode_to_json_stream, decode_from_json_stream


def main():
    """Main function for the CLI."""
    parser = argparse.ArgumentParser(
        description="tzBJC - TaggedZ's Binary JSON Converter. Encode or decode binary files to/from JSON."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Encode subcommand
    encode_parser = subparsers.add_parser("encode", help="Encode binary file to JSON")
    encode_parser.add_argument("--input", "-i", required=True, help="Input binary file path")
    encode_parser.add_argument("--output", "-o", help="Output JSON file path (default: stdout)")
    encode_parser.add_argument(
        "--force", "-f", action="store_true", 
        help="Overwrite output file if it already exists"
    )

    # Decode subcommand
    decode_parser = subparsers.add_parser("decode", help="Decode JSON to binary file")
    decode_parser.add_argument("--input", "-i", required=True, help="Input JSON file path")
    decode_parser.add_argument("--output", "-o", help="Output binary file path (default: use embedded filename)")
    decode_parser.add_argument(
        "--force", "-f", action="store_true",
        help="Overwrite output file if it already exists"
    )

    args = parser.parse_args()

    if args.command == "encode":
        try:
            if args.output:
                if os.path.exists(args.output) and not args.force:
                    print(f"Error: output file '{args.output}' already exists. Use --force to overwrite.")
                    sys.exit(1)
                with open(args.output, "w", encoding="utf-8") as out:
                    encode_to_json_stream(args.input, out)
            else:
                encode_to_json_stream(args.input, sys.stdout)
        except FileNotFoundError:
            print(f"Error: input file '{args.input}' not found.")
            sys.exit(1)

    elif args.command == "decode":
        with open(args.input, "r", encoding="utf-8") as infile:
            try:
                parsed = json.load(infile)
                output_path = args.output or parsed.get("filename")
                if not output_path:
                    print("Error: no output file specified and no filename found in JSON.")
                    sys.exit(1)

                if os.path.exists(output_path) and not args.force:
                    print(f"Error: output file '{output_path}' already exists. Use --force to overwrite.")
                    sys.exit(1)

                json_stream = StringIO(json.dumps(parsed))
                decode_from_json_stream(json_stream, output_path)

            except KeyError as e:
                print(f"Error: missing key in JSON: {e}")
                sys.exit(1)
            except (binascii.Error, zstd.ZstdError, ValueError) as e:
                print(f"Error during decoding: {e}")
                sys.exit(1)
