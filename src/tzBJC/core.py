import json

def binary_to_signed_json(binary_data: bytes) -> str:
    return json.dumps({"data": list(binary_data)})

def signed_json_to_binary(json_str: str) -> bytes:
    obj = json.loads(json_str)
    return bytes(obj["data"])
