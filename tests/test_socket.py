import json
import logging
from socket import socket
from unittest.mock import patch

import pytest
from vzenith_camera.socket import PacketHeader, BadPacketHeader, PACKET_TYPE_TEXT, PACKET_TYPE_HEARTBEAT
from vzenith_camera.socket import socket_send, socket_recv, socket_send_heartbeat


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


def test_socket_send(sock: socket):
    with patch.object(socket, 'send') as mock_send:
        body = {'cmd': 'test-cmd', 'params': {'key1': 'value1', 'key2': 1234, 'key3': True}}
        socket_send(sock, PACKET_TYPE_TEXT, body)

        buff = json.dumps(body, ensure_ascii=True).encode('ascii')
        mock_send.assert_called_with(b'VZ\x00\x00' + len(buff).to_bytes(4, 'big') + buff)


def test_socket_recv(sock: socket):
    body = {'cmd': 'test-cmd', 'state_code': 200, 'key1': 'value1', 'key2': 1234, 'key3': True}
    buff = json.dumps(body, ensure_ascii=True).encode('ascii')

    def recv_fn(n: int):
        if n == 8:
            return b'VZ\x00' + len(buff).to_bytes(4, 'big') + b'\x00'

        return buff

    with patch.object(socket, 'recv', side_effect=recv_fn), patch.object(logging, 'debug') as mock_debug:
        assert socket_recv(sock).body == body
        mock_debug.assert_called_with('recv %s from %s', buff, sock.getpeername())


def test_send_heartbeat(sock: socket):
    with patch.object(socket, 'send') as mock_send:
        socket_send_heartbeat(sock)
        mock_send.assert_called_with(b'VZ\x01\x00\x00\x00\x00\x00')
