import base64

from centralcli.ws_client import _decode


def test_decode_ip_from_int():
    # integer representation of 127.0.0.1
    assert _decode(0x7f000001, field_type="ip") == "127.0.0.1"


def test_decode_ip_from_base64_bytes():
    raw = b"\x0a\x00\x00\x01"  # 10.0.0.1
    b64 = base64.b64encode(raw).decode("ascii")
    assert _decode(b64, field_type="ip") == "10.0.0.1"


def test_decode_ip_from_dict_addr():
    raw = b"\xac\x10\x00\x01"  # 172.16.0.1
    b64 = base64.b64encode(raw).decode("ascii")
    msg = {"addrFamily": "ADDR_FAMILY_INET", "addr": b64}
    assert _decode(msg, field_type="ip") == "172.16.0.1"


def test_decode_ipv6_from_bytes():
    raw = bytes.fromhex("20010db8000000000000000000000001")  # 2001:db8::1
    b64 = base64.b64encode(raw).decode("ascii")
    assert _decode(b64, field_type="ip") == "2001:db8::1"
