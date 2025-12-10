from typing import Literal

import pytest  # type: ignore[import-not-found]


@pytest.fixture(scope="session")  # type: ignore[untyped-decorator]
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"
