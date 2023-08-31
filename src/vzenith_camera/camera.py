import logging
import time
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from .socket import PACKET_TYPE_TEXT, socket_send_heartbeat, socket_send, socket_recv


class BaseCamera:
    socket: socket

    name: str
    keepalive: bool = False

    def __init__(self, name: str):
        self.name = name
        self.socket = socket(AF_INET, SOCK_STREAM)

    def connect(self, address: tuple[str, int], keepalive: bool = False):
        logging.debug('connect to %s (%s)', self.name, address)
        self.socket.connect(address)
        self.keepalive = keepalive

        if keepalive:
            Thread(target=_thread_keepalive, name=f'thread-keepalive:{self.name}', args=(self,)).start()

    def heartbeat(self):
        socket_send_heartbeat(self.socket)


class SmartCamera(BaseCamera):
    def cmd_getsn(self) -> str:
        socket_send(self.socket, PACKET_TYPE_TEXT, {'cmd': 'getsn'})

        return socket_recv(self.socket).body['value']


def _thread_keepalive(camera: SmartCamera, interval: float = 5.0):
    while camera.keepalive:
        camera.heartbeat()
        time.sleep(interval)
