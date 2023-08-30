import pytest
from vzenith_camera.socket import PacketHeader, BadPacketHeader, PACKET_TYPE_TEXT, PACKET_TYPE_HEARTBEAT


def test_packet_header():
    s = b'VZ\x00\xab\x01\x02\x03\x04'
    header = PacketHeader.parse(s)

    assert header is not None
    assert header.type == PACKET_TYPE_TEXT
    assert header.length == 0x01020304
    assert header.sn == 0xab

    assert header.to_bytes() == s

    s = b'VZ\x01\x00\x01\x02\x03\x04'
    header = PacketHeader.parse(s)

    assert header.length == 0x01020304
    assert header.sn == 0x00

    # Inconsistency by design:
    # header.type should equal to HEARTBEAT even length isn't zero.
    assert header.type == PACKET_TYPE_HEARTBEAT
    assert header.to_bytes() == s

    s = b'12345678'
    with pytest.raises(BadPacketHeader):
        PacketHeader.parse(s)

    s = b'VZ'
    with pytest.raises(BadPacketHeader):
        PacketHeader.parse(s)
