from textwrap import dedent

from src.radon_lsp.server import RadonLanguageServer


def test_complexity_below_threshold(server: RadonLanguageServer) -> None:

    server.settings.threshold = 10

    diagnostics = []

    blocks = server.analyze_complexity(
        dedent("""
        def simple():
            return 1
        """),
        diagnostics,
    )

    assert len(blocks) == 1
    assert diagnostics == []


def test_complexity_warning(server: RadonLanguageServer) -> None:

    server.settings.threshold = 2
    server.settings.error_threshold = 10

    diagnostics = []

    server.analyze_complexity(
        dedent("""
        def example(x):
            if x > 10:
                return 1
            return 2
        """),
        diagnostics,
    )

    assert len(diagnostics) == 1

    diagnostic = diagnostics[0]

    assert diagnostic.severity.name == "Warning"
    assert diagnostic.code == "radon-complexity"
    assert "cyclomatic complexity" in diagnostic.message


def test_complexity_error(server: RadonLanguageServer) -> None:

    server.settings.threshold = 1
    server.settings.error_threshold = 2

    diagnostics = []

    server.analyze_complexity(
        dedent("""
        def example(x):
            if x:
                if x > 10:
                    if x > 20:
                        return 1
            return 2
        """),
        diagnostics,
    )

    assert any(diagnostic.severity.name == "Error" for diagnostic in diagnostics)


def test_complexity_includes_grade(server: RadonLanguageServer) -> None:

    server.settings.threshold = 1
    server.settings.show_grade = True

    diagnostics = []

    server.analyze_complexity(
        dedent("""
        def example(x):
            if x:
                return 1
            return 2
        """),
        diagnostics,
    )

    assert "grade" in diagnostics[0].message


def test_complexity_excludes_grade(server: RadonLanguageServer) -> None:

    server.settings.threshold = 1
    server.settings.show_grade = False

    diagnostics = []

    server.analyze_complexity(
        dedent("""
        def example(x):
            if x:
                return 1
            return 2
        """),
        diagnostics,
    )

    assert "grade" not in diagnostics[0].message
