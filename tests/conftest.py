import pytest

from radon_lsp.server import RadonLanguageServer


@pytest.fixture(scope="function")
def server() -> RadonLanguageServer:
    return RadonLanguageServer()
