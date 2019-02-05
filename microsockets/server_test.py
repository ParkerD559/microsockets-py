import pytest
import asyncio
import websockets
from time import sleep
from .server import MicroServer


@pytest.fixture()
async def app():
    app = MicroServer()
    yield app
    await app.close()


@pytest.fixture()
async def running_app(app):
    await app.run()
    yield app


@pytest.fixture()
async def async_stub(mocker):
    stub = mocker.MagicMock(return_value=asyncio.Future())
    stub.return_value.set_result({"status":1})
    return stub


@pytest.mark.asyncio
async def test_run_defaults(app):
    await app.run()
    async with websockets.connect('ws://localhost:8765') as websocket:
        assert websocket.open


@pytest.mark.asyncio
async def test_run_port(app):
    port = '8000'
    await app.run(port=port)
    async with websockets.connect('ws://localhost:' + port) as websocket:
        assert websocket.open


@pytest.mark.asyncio
async def test_handler_exists(running_app, async_stub):
    running_app.register(key='TestKey')(async_stub)

    async with websockets.connect('ws://localhost:8765') as websocket:
        await websocket.send('{"type":"TestKey"}')
        await websocket.recv()

    assert async_stub.call_count == 1


@pytest.mark.asyncio
async def test_handler_not_exists(running_app, async_stub):
    running_app.register(key='TestKey')(async_stub)

    async with websockets.connect('ws://localhost:8765') as websocket:
        await websocket.send('{"type":"WrongKey"}')

    assert async_stub.call_count == 0


@pytest.mark.asyncio
async def test_register_handlers(running_app, async_stub):
    class MockHandlers(object):
        pass

    mockHandlers = MockHandlers()
    mockHandlers.handlers = {'TestKey':async_stub}

    running_app.register_handlers(mockHandlers)

    async with websockets.connect('ws://localhost:8765') as websocket:
        await websocket.send('{"type":"TestKey"}')
        await websocket.recv()

    assert async_stub.call_count == 1