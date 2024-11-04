import json
import logging
import time
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from typing import Tuple

from .emitter import Emitter
from .socket import BadPacketHeader, socket_send_heartbeat, socket_send, socket_recv
from .socket import PACKET_TYPE_TEXT, PACKET_TYPE_HEARTBEAT, TEXT_ENCODING
from .types import PlateResult


class BaseCamera(Emitter):
    socket: socket

    name: str
    keepalive: bool = False

    def __init__(self, name: str):
        super().__init__()

        self.name = name
        self.socket = socket(AF_INET, SOCK_STREAM)

    def connect(self, address: Tuple[str, int], keepalive: bool = False):
        logging.debug('connect to %s (%s)', self.name, address)
        self.socket.connect(address)
        self.keepalive = keepalive

        if keepalive:
            Thread(target=self._keepalive_thread, name=f'keepalive:{self.name}').start()

    def heartbeat(self):
        socket_send_heartbeat(self.socket)

    def _keepalive_thread(self, interval: float = 5.0):
        while self.keepalive:
            self.heartbeat()
            time.sleep(interval)


class SmartCamera(BaseCamera):
    ivsresult_enabled: bool

    def cmd_getsn(self) -> str:
        socket_send(self.socket, PACKET_TYPE_TEXT, {'cmd': 'getsn'})

        res = json.loads(socket_recv(self.socket, skip_heartbeat=True).body.decode(TEXT_ENCODING))

        check_response_status(res)

        return res['value']

    def cmd_getivsresult(self, image: bool = False, result_format: str = 'json'):
        socket_send(self.socket, PACKET_TYPE_TEXT, {'cmd': 'getivsresult', 'image': image, 'format': result_format})

        while True:
            packet = socket_recv(self.socket)

            if packet.header.type == PACKET_TYPE_HEARTBEAT:
                continue

            s = packet.body
            res = json.loads(s[0:s.index(0x00) - 1].decode(TEXT_ENCODING))['PlateResult']

            return PlateResult(
                license=res['license']
            )

    def cmd_ivsresult(self, enable: bool = False, result_format: str = 'json', image: bool = True, image_type: int = 0):
        cmd = {
            'cmd': 'ivsresult',
            'enable': enable,
            'format': result_format,
            'image': image,
            'image_type': image_type
        }

        socket_send(self.socket, PACKET_TYPE_TEXT, cmd)
        socket_recv(self.socket, skip_heartbeat=True)

        if enable:
            self.ivsresult_enabled = True
            Thread(target=self._ivsresult_thread, name=f'ivsresult:{self.name}').start()

    def _ivsresult_thread(self):
        while self.ivsresult_enabled:
            try:
                packet = socket_recv(self.socket, blocking=False, skip_heartbeat=True)

                pr = json.loads(packet.body[0:packet.body.index(0x00) - 1].decode('gb2312'))['PlateResult']
                result = PlateResult(
                    license=pr['license'],
                )

                self.emit('ivsresult', result)
            except (BlockingIOError, BadPacketHeader):
                ...

            time.sleep(1)


def check_response_status(res: dict):
    if 'state_code' not in res:
        raise BadResponse(res)

    if res['state_code'] == 400:
        raise BadRequest(res)
    if res['state_code'] == 401:
        raise Unauthorized(res)
    if res['state_code'] == 404:
        raise NotFound(res)
    if res['state_code'] == 405:
        raise MethodNotAllowed(res)
    if res['state_code'] == 408:
        raise RequestTimeout(res)
    if res['state_code'] == 500:
        raise InternalServerError(res)


class BadResponse(ValueError):
    ...


class ResponseError(RuntimeError):
    ...


class BadRequest(ResponseError):
    ...


class Unauthorized(ResponseError):
    ...


class NotFound(ResponseError):
    ...


class MethodNotAllowed(ResponseError):
    ...


class RequestTimeout(ResponseError):
    ...


class InternalServerError(ResponseError):
    ...
