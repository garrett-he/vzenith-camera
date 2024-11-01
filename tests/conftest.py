from socket import socket, AF_INET, SOCK_STREAM
from unittest.mock import patch

import pytest
from vzenith_camera.camera import SmartCamera


@pytest.fixture(scope='module')
def sock():
    s = socket(AF_INET, SOCK_STREAM)

    with patch.object(socket, 'connect'), patch.object(socket, 'getpeername', return_value=('1.2.3.4', 1234)):
        s.connect(('1.2.3.4', 1234))
        yield s


@pytest.fixture(scope='module')
def camera():
    result = SmartCamera('test-camera')

    with patch.object(socket, 'connect') as connect_mock:
        with patch.object(socket, 'getpeername', return_value=('1.2.3.4', 1234)):
            result.connect(('127.0.0.1', 1234))

            connect_mock.assert_called_with(('127.0.0.1', 1234))

            assert result.name == 'test-camera'

            yield result
