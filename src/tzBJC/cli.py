import argparse
from .core import binary_to_signed_json, signed_json_to_binary

def main():
    parser = argparse.ArgumentParser(description="Convert binary <-> signed JSON")
    parser.add_argument("input", help="Input file")
    parser.add_argument("output", help="Output file")
    parser.add_argument("--to-json", action="store_true", help="Convert binary to signed JSON")
    args = parser.parse_args()

    if args.to_json:
        with open(args.input, "rb") as f:
            data = f.read()
        json_str = binary_to_signed_json(data)
        with open(args.output, "w") as f:
            f.write(json_str)
    else:
        with open(args.input, "r") as f:
            json_str = f.read()
        data = signed_json_to_binary(json_str)
        with open(args.output, "wb") as f:
            f.write(data)
