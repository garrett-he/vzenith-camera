from __future__ import annotations
import json
import logging
import struct
from dataclasses import dataclass
from socket import socket
from typing import Any, Optional

PACKET_TYPE_TEXT = 0
PACKET_TYPE_HEARTBEAT = 1
PACKET_TYPE_BINARY = 2

TEXT_ENCODING = 'gb2312'


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


@dataclass
class Packet:
    header: PacketHeader
    body: Optional[Any]


class BadPacketHeader(ValueError):
    ...


def socket_send_buffer(sock: socket, buff: bytes):
    logging.debug('send %s to %s', buff, sock.getpeername())
    sock.send(buff)


def socket_recv_buffer(sock: socket, n: int, blocking: bool = True) -> bytes:
    sock.setblocking(blocking)

    buff = sock.recv(n)
    logging.debug('recv %s from %s', buff, sock.getpeername())

    return buff


def socket_recv_header(sock: socket, blocking: bool = True) -> PacketHeader:
    return PacketHeader.parse(socket_recv_buffer(sock, 8, blocking))


def socket_send(sock: socket, packet_type: int, body: Optional[Any] = None, sn: int = 0):
    buff = json.dumps(body, ensure_ascii=True).encode('ascii') if body is not None else b''
    header = PacketHeader(type=packet_type, sn=sn, length=len(buff)).to_bytes()

    socket_send_buffer(sock, header + buff)


def socket_recv(sock: socket, blocking: bool = True, skip_heartbeat: bool = False) -> Packet:
    header = socket_recv_header(sock, blocking)
    if skip_heartbeat and header.type == PACKET_TYPE_HEARTBEAT:
        header = socket_recv_header(sock, blocking)

    body = socket_recv_buffer(sock, header.length, blocking) if header.type != PACKET_TYPE_HEARTBEAT else None

    return Packet(header=header, body=body)


def socket_send_heartbeat(sock: socket):
    socket_send_buffer(sock, PacketHeader(type=PACKET_TYPE_HEARTBEAT, sn=0, length=0).to_bytes())
