from __future__ import annotations
import struct
from dataclasses import dataclass

PACKET_TYPE_TEXT = 0
PACKET_TYPE_HEARTBEAT = 1
PACKET_TYPE_BINARY = 2


@dataclass
class PacketHeader:
    type: int
    sn: int
    length: int

    def to_bytes(self) -> bytes:
        return struct.pack('!2sBBI', b'VZ', self.type, self.sn, self.length)

    @staticmethod
    def parse(s: bytes) -> PacketHeader:
        if len(s) != 8 or s[0:2] != b'VZ':
            raise BadPacketHeader(s)

        return PacketHeader(*struct.unpack('!2xBBI', s))


class BadPacketHeader(ValueError):
    ...
