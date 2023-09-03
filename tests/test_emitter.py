from unittest.mock import Mock

from vzenith_camera.emitter import Event, Emitter


class TestEmitter(Emitter):
    __test__ = False


def test_emitter():
    listener = Mock(return_value=None)

    emitter = TestEmitter()
    emitter.on('test-event', listener)

    assert emitter.emit('test-event', 'test')
    listener.assert_called_with(Event(name='test-event', target=emitter), 'test')

    assert not emitter.emit('invalid-event')


def test_event_listener_call_once():
    listener = Mock(return_value=None)

    emitter1 = TestEmitter()
    emitter1.on('test-event', listener)

    emitter2 = TestEmitter()
    emitter2.on('test-event', listener)

    assert emitter1.emit('test-event')
    listener.assert_called_once()
