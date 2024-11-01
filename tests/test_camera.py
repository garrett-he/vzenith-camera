import json
from socket import socket
from threading import Thread
from unittest.mock import patch

from vzenith_camera.socket import TEXT_ENCODING
from vzenith_camera.camera import SmartCamera


def test_camera_heartbeat(camera: SmartCamera):
    with patch.object(socket, 'send') as send_mock:
        with patch.object(socket, 'recv', return_value=b'VZ\x01\x00\x00\x00\x00\x00'):
            camera.heartbeat()

            send_mock.assert_called_with(b'VZ\x01\x00\x00\x00\x00\x00')


def test_camera_keepalive():
    camera = SmartCamera('test-keepalive')

    with patch.object(socket, 'connect'):
        with patch.object(Thread, 'start') as thread_start_mock:
            camera.connect(('127.0.0.1', 8131), True)
            thread_start_mock.assert_called_once()

        with patch.object(camera, 'heartbeat') as heartbeat_mock:
            camera.connect(('127.0.0.1', 8131), True)
            heartbeat_mock.assert_called()

            camera.keepalive = False


def test_camera_cmd_getsn(camera: SmartCamera):
    body = {'cmd': 'getsn', 'error_msg': 'Sucess', 'id': '999999', 'state_code': 200, 'value': '00000000-ffffffff'}
    buff = json.dumps(body, ensure_ascii=True).encode(TEXT_ENCODING)

    def recv_fn(n: int):
        if n == 8:
            return b'VZ\x00\x00' + len(buff).to_bytes(4, 'big')

        return buff

    with patch.object(socket, 'send') as send_mock:
        with patch.object(socket, 'recv', side_effect=recv_fn):
            assert camera.cmd_getsn() == '00000000-ffffffff'

            send_mock.assert_called_with(b'VZ\x00\x00\x00\x00\x00\x10{"cmd": "getsn"}')
