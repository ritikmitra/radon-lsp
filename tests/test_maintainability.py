from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from lsprotocol.types import MarkupContent, Position

from src.radon_lsp.server import RadonLanguageServer


def test_maintainability_above_threshold(server: RadonLanguageServer) -> None:

    diagnostics = []

    with patch(
        "src.radon_lsp.server.mi_visit",
        return_value=80.0,
    ):
        result = server.analyze_maintainability(
            "x = 1",
            diagnostics,
        )

    assert result == 80.0
    assert diagnostics == []


def test_maintainability_raise_exception(server: RadonLanguageServer) -> None:

    diagnostics = []

    with patch("src.radon_lsp.server.mi_visit", side_effect=RuntimeError("test error")):
        result = server.analyze_maintainability(
            """def hello():
                return 1
            """,
            diagnostics,
        )

    assert result == None


def test_add_maintainbility_diagnostics_empty_list(server: RadonLanguageServer) -> None:

    result = server._add_maintainability_diagnostics(None, [])

    assert result is None


def test_add_maintainability_diagnostics(server: RadonLanguageServer) -> None:

    diagnostics = []

    item_without_mi = MagicMock()
    item_without_mi.mi = None

    item_with_mi = MagicMock()
    item_with_mi.mi = 75.5
    item_with_mi.name = "hello"
    item_with_mi.lineno = 3

    result = [
        item_without_mi,
        item_with_mi,
    ]

    with patch.object(server, "_add_mi_diagnostic") as mock_add:
        server._add_maintainability_diagnostics(
            result,
            diagnostics,
        )

    mock_add.assert_called_once_with(
        name="hello",
        lineno=3,
        mi=75.5,
        diagnostics=diagnostics,
    )


def test_low_maintainability_creates_warning(server: RadonLanguageServer) -> None:

    diagnostics = []

    with patch(
        "src.radon_lsp.server.mi_visit",
        return_value=60.0,
    ):
        server.analyze_maintainability(
            "x = 1",
            diagnostics,
        )

    assert len(diagnostics) == 1

    diagnostic = diagnostics[0]

    assert diagnostic.code == "radon-maintainability"
    assert diagnostic.severity.name == "Warning"
    assert "low maintainability index" in diagnostic.message


def test_very_low_maintainability_creates_error(server: RadonLanguageServer) -> None:

    diagnostics = []

    with patch(
        "src.radon_lsp.server.mi_visit",
        return_value=40.0,
    ):
        server.analyze_maintainability(
            "x = 1",
            diagnostics,
        )

    assert len(diagnostics) == 1
    assert diagnostics[0].severity.name == "Error"


def test_block_range(server: RadonLanguageServer) -> None:
    block = SimpleNamespace(
        lineno=5,
        endline=10,
    )

    result = RadonLanguageServer.block_range(block)

    assert result.start.line == 4
    assert result.start.character == 0

    assert result.end.line == 9
    assert result.end.character == 1000


def test_hover_on_function(server: RadonLanguageServer) -> None:

    uri = "file:///test.py"

    server.analyze(
        uri,
        """
def hello():
    return 1
""",
    )

    hover = server.get_hover(
        uri,
        Position(line=1, character=0),
    )

    assert hover is not None
    contents = hover.contents

    assert isinstance(contents, MarkupContent)

    assert "hello" in contents.value
    assert "complexity" in contents.value


def test_hover_outside_function_declaration_returns_none(
    server: RadonLanguageServer,
) -> None:

    uri = "file:///test.py"

    server.analyze(
        uri,
        """
def hello():
    x = 1
    return x
""",
    )

    hover = server.get_hover(
        uri,
        Position(line=2, character=0),
    )

    assert hover is None


def test_syntax_error_clears_analysis(server: RadonLanguageServer) -> None:

    uri = "file:///test.py"

    with patch.object(server, "publish_diagnostics") as publish:
        server.analyze(
            uri,
            """
def broken(
    this is invalid python
""",
        )

    assert uri not in server.blocks
    assert uri not in server.maintainability

    publish.assert_called_once_with(uri, [])


def test_analyze_publishes_diagnostics(server: RadonLanguageServer) -> None:

    uri = "file:///test.py"

    with patch.object(server, "publish_diagnostics") as publish:
        server.analyze(
            uri,
            """
def foo(x):
    if x:
        return 1
    return 2
""",
        )

    assert uri in server.blocks
    assert uri in server.maintainability

    publish.assert_called_once()

    args = publish.call_args.args

    assert args[0] == uri
    assert isinstance(args[1], list)
