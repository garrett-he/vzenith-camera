import json
from socket import socket
from threading import Thread
from unittest.mock import patch

import pytest
from vzenith_camera.socket import TEXT_ENCODING
from vzenith_camera.camera import SmartCamera, BadRequest, BadResponse, Unauthorized, NotFound, MethodNotAllowed, \
    RequestTimeout, InternalServerError, check_response_status
from vzenith_camera.emitter import Event
from vzenith_camera.types import PlateResult


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


def test_camera_cmd_getivsresult(camera: SmartCamera):
    buff = json.dumps({'PlateResult': {'license': 'T12345'}}).encode(TEXT_ENCODING) + b'\n\x00'

    def recv_fn(n: int):
        if n == 8:
            return b'VZ\x00\x00' + len(buff).to_bytes(4, 'big')

        return buff

    with patch.object(socket, 'send') as send_mock:
        with patch.object(socket, 'recv', side_effect=recv_fn):
            assert camera.cmd_getivsresult().license == 'T12345'

            send_mock.assert_called_with(
                b'VZ\x00\x00\x00\x00\x009{"cmd": "getivsresult", "image": false, "format": "json"}')


def test_camera_cmd_ivsresult(camera: SmartCamera):
    req_body = json.dumps({
        'cmd': 'ivsresult',
        'enable': True,
        'format': 'json',
        'image': True,
        'image_type': 0
    }).encode(TEXT_ENCODING)
    req_header = b'VZ\x00\x00' + len(req_body).to_bytes(4, 'big')

    res_body = json.dumps({'cmd': 'ivsresult', 'state_code': 200}).encode(TEXT_ENCODING)
    res_header = b'VZ\x00\x00' + len(res_body).to_bytes(4, 'big')

    def recv_fn(n: int):
        if n == 8:
            return res_header

        return res_body

    with patch.object(socket, 'send') as send_mock:
        with patch.object(socket, 'recv', side_effect=recv_fn):
            with patch.object(Thread, 'start') as thread_start_mock:
                camera.cmd_ivsresult(True)

                send_mock.assert_called_with(req_header + req_body)
                thread_start_mock.assert_called_once()


def test_camera_ivsresult_thread(camera: SmartCamera):
    res_body = json.dumps({'PlateResult': {'license': 'T12345'}}).encode(TEXT_ENCODING) + b'\n\x00'
    res_header = b'VZ\x00\x00' + len(res_body).to_bytes(4, 'big')

    def recv_fn(*args, **_):
        if args[0] == 8:
            return res_header

        return res_body

    def ivsresult_callback(event: Event, plate_result: PlateResult):
        assert event.target == camera
        assert plate_result.license == 'T12345'

        camera.ivsresult_enabled = False

    camera.on('ivsresult', ivsresult_callback)

    with patch.object(socket, 'send'):
        with patch.object(socket, 'recv', side_effect=recv_fn):
            camera.cmd_ivsresult(True)


def test_check_response_status():
    res = {}
    with pytest.raises(BadResponse):
        check_response_status(res)

    res = {'state_code': 400}
    with pytest.raises(BadRequest):
        check_response_status(res)

    res = {'state_code': 401}
    with pytest.raises(Unauthorized):
        check_response_status(res)

    res = {'state_code': 404}
    with pytest.raises(NotFound):
        check_response_status(res)

    res = {'state_code': 405}
    with pytest.raises(MethodNotAllowed):
        check_response_status(res)

    res = {'state_code': 408}
    with pytest.raises(RequestTimeout):
        check_response_status(res)

    res = {'state_code': 500}
    with pytest.raises(InternalServerError):
        check_response_status(res)
