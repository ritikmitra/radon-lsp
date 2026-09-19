import pytest

from src.radon_lsp.server import RadonLanguageServer


@pytest.fixture(scope="function")
def server() -> RadonLanguageServer:
    return RadonLanguageServer()
