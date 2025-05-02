from binaryjsonconverter.core import binary_to_signed_json, signed_json_to_binary

def test_binary_json_roundtrip():
    data = b"hello world"
    json_str = binary_to_signed_json(data)
    restored = signed_json_to_binary(json_str)
    assert restored == data
