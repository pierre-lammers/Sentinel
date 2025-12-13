from typing import Literal

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"
