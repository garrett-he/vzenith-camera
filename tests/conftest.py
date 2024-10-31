from socket import socket, AF_INET, SOCK_STREAM
from unittest.mock import patch

import pytest


@pytest.fixture(scope='module')
def sock():
    s = socket(AF_INET, SOCK_STREAM)

    with patch.object(socket, 'connect'), patch.object(socket, 'getpeername', return_value=('1.2.3.4', 1234)):
        s.connect(('1.2.3.4', 1234))
        yield s
