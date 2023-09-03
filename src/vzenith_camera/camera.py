import json
import logging
import time
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from typing import Tuple

from .socket import PACKET_TYPE_TEXT, TEXT_ENCODING, socket_send_heartbeat, socket_send, socket_recv
from .types import PlateResult


class BaseCamera:
    socket: socket

    name: str
    keepalive: bool = False

    def __init__(self, name: str):
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
    def cmd_getsn(self) -> str:
        socket_send(self.socket, PACKET_TYPE_TEXT, {'cmd': 'getsn'})

        return json.loads(socket_recv(self.socket).body.decode(TEXT_ENCODING))['value']

    def cmd_getivsresult(self, image: bool = False, result_format: str = 'json'):
        socket_send(self.socket, PACKET_TYPE_TEXT, {'cmd': 'getivsresult', 'image': image, 'format': result_format})
        s = socket_recv(self.socket).body
        print(s)
        res = json.loads(s[0:s.index(0x00) - 1].decode(TEXT_ENCODING))['PlateResult']

        return PlateResult(
            license=res['license']
        )
