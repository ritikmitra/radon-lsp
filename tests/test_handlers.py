from textwrap import dedent
from unittest.mock import MagicMock, patch

from lsprotocol.types import (
    DidChangeConfigurationParams,
    DidCloseTextDocumentParams,
    TextDocumentIdentifier,
)

from radon_lsp.server import (
    RadonLanguageServer,
    did_change_configuration,
    did_close,
    initialize,
)


def test_configure_with_radon_wrapper(server: RadonLanguageServer) -> None:

    server.configure(
        {
            "radon": {
                "threshold": 3,
            }
        }
    )

    assert server.settings.threshold == 3


def test_initialize_applies_initialization_options(
    server: RadonLanguageServer,
) -> None:

    params = MagicMock(initialization_options={"threshold": 4})

    initialize(server, params)

    assert server.settings.threshold == 4


def test_did_change_configuration_reanalyzes(server: RadonLanguageServer) -> None:

    params = DidChangeConfigurationParams(settings={"threshold": 7})

    with patch.object(server, "reanalyze_open_documents") as reanalyze:
        did_change_configuration(server, params)

    assert server.settings.threshold == 7
    reanalyze.assert_called_once_with()


def test_reanalyze_open_documents(server: RadonLanguageServer) -> None:

    document = MagicMock(
        uri="file:///test.py",
        source=dedent("""
        def simple():
            return 1
        """),
    )

    with (
        patch.object(
            type(server),
            "workspace",
            new_callable=lambda: property(
                lambda _: MagicMock(text_documents={document.uri: document})
            ),
        ),
        patch.object(server, "analyze") as analyze,
    ):
        server.reanalyze_open_documents()

    analyze.assert_called_once_with(document.uri, document.source)


def test_did_close_clears_state(server: RadonLanguageServer) -> None:

    uri = "file:///test.py"
    server.blocks[uri] = [MagicMock()]
    server.maintainability[uri] = 80.0

    params = DidCloseTextDocumentParams(
        text_document=TextDocumentIdentifier(uri=uri),
    )

    with patch.object(server, "publish_diagnostics") as publish:
        did_close(server, params)

    assert uri not in server.blocks
    assert uri not in server.maintainability
    publish.assert_called_once_with(uri, [])
