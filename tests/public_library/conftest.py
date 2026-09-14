import socket
import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn


@pytest.fixture(scope="module")
def public_url() -> Iterator[str]:
    pytest.importorskip("mcp")
    from app.public_library.app import create_app
    from app.public_library.settings import PublicSettings

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        app = create_app(PublicSettings(base_url=url))
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    raise RuntimeError("Public library test server did not start.")
                time.sleep(0.01)
            yield url
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive(), "Public library test server did not stop."
