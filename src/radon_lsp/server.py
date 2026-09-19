from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from lsprotocol.types import (
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    TEXT_DOCUMENT_HOVER,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    Hover,
    MarkupContent,
    MarkupKind,
    Position,
    PublishDiagnosticsParams,
    Range,
)
from pygls.lsp.server import LanguageServer
from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_visit

logger = logging.getLogger("radon-lsp")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class RadonSettings:
    """
    Radon configuration.

    Zed example:

    {
        "lsp": {
            "radon": {
                "settings": {
                    "threshold": 10,
                    "error_threshold": 20,
                    "enable_complexity": true,
                    "enable_maintainability": true,
                    "maintainability_threshold": 65,
                    "maintainability_error_threshold": 50,
                    "show_grade": true
                }
            }
        }
    }
    """

    # Cyclomatic complexity
    threshold: int = 10
    error_threshold: int = 20

    # Features
    enable_complexity: bool = True
    enable_maintainability: bool = True

    # Maintainability Index
    maintainability_threshold: float = 65.0
    maintainability_error_threshold: float = 50.0

    # UI
    show_grade: bool = True

    @classmethod
    def from_dict(
        cls,
        settings: dict[str, Any] | None,
    ) -> RadonSettings:
        if not settings:
            return cls()

        return cls(
            threshold=_int(
                settings.get("threshold"),
                cls.threshold,
            ),
            error_threshold=_int(
                settings.get("error_threshold"),
                cls.error_threshold,
            ),
            enable_complexity=_bool(
                settings.get("enable_complexity"),
                cls.enable_complexity,
            ),
            enable_maintainability=_bool(
                settings.get("enable_maintainability"),
                cls.enable_maintainability,
            ),
            maintainability_threshold=_float(
                settings.get("maintainability_threshold"),
                cls.maintainability_threshold,
            ),
            maintainability_error_threshold=_float(
                settings.get("maintainability_error_threshold"),
                cls.maintainability_error_threshold,
            ),
            show_grade=_bool(
                settings.get("show_grade"),
                cls.show_grade,
            ),
        )


def _int(value: Any, default: int) -> int:
    try:
        return default if value is None else int(value)
    except TypeError, ValueError:
        return default


def _float(value: Any, default: float) -> float:
    try:
        return default if value is None else float(value)
    except TypeError, ValueError:
        return default


def _bool(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


# ---------------------------------------------------------------------------
# Language Server
# ---------------------------------------------------------------------------


class RadonLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__(
            name="radon-lsp",
            version="0.1.0",
        )

        self.settings = RadonSettings()

        # URI -> Radon complexity blocks
        self.blocks: dict[str, list[Any]] = {}

        # URI -> maintainability result
        self.maintainability: dict[str, Any] = {}

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------

    def configure(self, initialization_options: Any):
        """
        Configure the server from Zed's initialization options.

        Supports both:

            {
                "threshold": 10
            }

        and:

            {
                "settings": {
                    "threshold": 10
                }
            }
        """

        if not isinstance(initialization_options, dict):
            return

        settings = initialization_options.get(
            "settings",
            initialization_options,
        )

        if not isinstance(settings, dict):
            return

        self.settings = RadonSettings.from_dict(settings)

        logger.info(
            "Configured Radon: threshold=%d, error_threshold=%d",
            self.settings.threshold,
            self.settings.error_threshold,
        )

    # -----------------------------------------------------------------------
    # Diagnostics
    # -----------------------------------------------------------------------

    def publish_diagnostics(
        self,
        uri: str,
        diagnostics: list[Diagnostic],
    ):
        self.text_document_publish_diagnostics(
            PublishDiagnosticsParams(
                uri=uri,
                diagnostics=diagnostics,
            )
        )

    @staticmethod
    def make_diagnostic(
        *,
        range_: Range,
        message: str,
        severity: DiagnosticSeverity,
        code: str,
    ) -> Diagnostic:
        return Diagnostic(
            range=range_,
            message=message,
            severity=severity,
            source="radon",
            code=code,
        )

    # -----------------------------------------------------------------------
    # Ranges
    # -----------------------------------------------------------------------

    @staticmethod
    def block_range(block: Any) -> Range:
        start_line = max(
            getattr(block, "lineno", 1) - 1,
            0,
        )

        end_line = getattr(
            block,
            "endline",
            getattr(block, "lineno", 1),
        )

        end_line = max(
            end_line - 1,
            start_line,
        )

        return Range(
            start=Position(
                line=start_line,
                character=0,
            ),
            end=Position(
                line=end_line,
                character=1000,
            ),
        )

    # -----------------------------------------------------------------------
    # Complexity analysis
    # -----------------------------------------------------------------------

    def analyze_complexity(
        self,
        source: str,
        diagnostics: list[Diagnostic],
    ) -> list[Any]:
        blocks = cc_visit(source)

        for block in blocks:
            complexity = block.complexity

            if complexity < self.settings.threshold:
                continue

            if complexity >= self.settings.error_threshold:
                severity = DiagnosticSeverity.Error
            else:
                severity = DiagnosticSeverity.Warning

            name = getattr(
                block,
                "name",
                "<unknown>",
            )

            rank = cc_rank(complexity)

            if self.settings.show_grade:
                message = f"{name}: cyclomatic complexity {complexity} (grade {rank})"
            else:
                message = f"{name}: cyclomatic complexity {complexity}"

            diagnostics.append(
                self.make_diagnostic(
                    range_=self.block_range(block),
                    message=message,
                    severity=severity,
                    code="radon-complexity",
                )
            )

        return blocks

    # -----------------------------------------------------------------------
    # Maintainability analysis
    # -----------------------------------------------------------------------

    def analyze_maintainability(
        self,
        source: str,
        diagnostics: list[Diagnostic],
    ):
        try:
            result = mi_visit(
                source,
                multi=True,
            )
        except Exception:
            logger.exception("Failed to calculate maintainability index")
            return None

        self._add_maintainability_diagnostics(
            result,
            diagnostics,
        )

        return result

    def _add_maintainability_diagnostics(
        self,
        result: Any,
        diagnostics: list[Diagnostic],
    ):
        if isinstance(result, (int, float)):
            self._add_mi_diagnostic(
                name="module",
                lineno=1,
                mi=float(result),
                diagnostics=diagnostics,
            )
            return

        if not isinstance(result, list):
            return

        for item in result:
            mi = getattr(
                item,
                "mi",
                None,
            )

            if mi is None:
                continue

            self._add_mi_diagnostic(
                name=getattr(item, "name", "module"),
                lineno=getattr(item, "lineno", 1),
                mi=float(mi),
                diagnostics=diagnostics,
            )

    def _add_mi_diagnostic(
        self,
        *,
        name: str,
        lineno: int,
        mi: float,
        diagnostics: list[Diagnostic],
    ):
        if mi > self.settings.maintainability_threshold:
            return

        severity = (
            DiagnosticSeverity.Error
            if mi <= self.settings.maintainability_error_threshold
            else DiagnosticSeverity.Warning
        )

        diagnostics.append(
            self.make_diagnostic(
                range_=Range(
                    start=Position(
                        line=max(lineno - 1, 0),
                        character=0,
                    ),
                    end=Position(
                        line=max(lineno - 1, 0),
                        character=1,
                    ),
                ),
                message=(f"{name}: low maintainability index ({mi:.1f}/100)"),
                severity=severity,
                code="radon-maintainability",
            )
        )

    # -----------------------------------------------------------------------
    # Complete analysis
    # -----------------------------------------------------------------------

    def analyze(
        self,
        uri: str,
        source: str,
    ):
        diagnostics: list[Diagnostic] = []

        try:
            if self.settings.enable_complexity:
                blocks = self.analyze_complexity(
                    source,
                    diagnostics,
                )
            else:
                blocks = cc_visit(source)

        except SyntaxError:
            # Let the Python language server own syntax diagnostics.
            self.blocks.pop(uri, None)
            self.maintainability.pop(uri, None)

            self.publish_diagnostics(
                uri,
                [],
            )
            return

        self.blocks[uri] = blocks

        if self.settings.enable_maintainability:
            self.maintainability[uri] = self.analyze_maintainability(
                source,
                diagnostics,
            )
        else:
            self.maintainability.pop(uri, None)

        self.publish_diagnostics(
            uri,
            diagnostics,
        )

    # -----------------------------------------------------------------------
    # Hover
    # -----------------------------------------------------------------------

    def get_hover(
        self,
        uri: str,
        position: Position,
    ) -> Hover | None:
        blocks = self.blocks.get(uri)

        if not blocks:
            return None

        line = position.line

        for block in blocks:
            start_line = max(
                getattr(block, "lineno", 1) - 1,
                0,
            )

            # Only trigger on the function's own declaration line,
            # not anywhere inside its body -- this matches where the
            # diagnostic itself is anchored and avoids a hover firing
            # on every single line of a long function.
            if line == start_line:
                return self._create_hover(
                    uri,
                    block,
                )

        return None

    def _create_hover(
        self,
        uri: str,
        block: Any,
    ) -> Hover:
        name = getattr(
            block,
            "name",
            "<unknown>",
        )

        complexity = block.complexity
        grade = cc_rank(complexity)

        if self.settings.show_grade:
            summary = f"complexity {complexity} ({grade})"
        else:
            summary = f"complexity {complexity}"

        # Only mention maintainability when it's actually low enough
        # to be worth flagging -- otherwise it's just noise on every
        # perfectly healthy function.
        mi = self._find_maintainability(
            uri,
            block,
        )

        if mi is not None and mi <= self.settings.maintainability_threshold:
            summary += f", maintainability {mi:.0f}/100"

        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.PlainText,
                value=f"{name}: {summary}",
            )
        )

    # -----------------------------------------------------------------------
    # Maintainability lookup
    # -----------------------------------------------------------------------

    def _find_maintainability(
        self,
        uri: str,
        block: Any,
    ) -> float | None:
        result = self.maintainability.get(uri)

        if result is None:
            return None

        if isinstance(result, (int, float)):
            return float(result)

        if not isinstance(result, list):
            return None

        name = getattr(
            block,
            "name",
            None,
        )

        lineno = getattr(
            block,
            "lineno",
            None,
        )

        for item in result:
            if (
                getattr(item, "name", None) == name
                and getattr(item, "lineno", None) == lineno
            ):
                mi = getattr(
                    item,
                    "mi",
                    None,
                )

                if mi is not None:
                    return float(mi)

        return None


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

server = RadonLanguageServer()


# ---------------------------------------------------------------------------
# Document events
# ---------------------------------------------------------------------------


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(
    ls: RadonLanguageServer,
    params: DidOpenTextDocumentParams,
):
    document = ls.workspace.get_text_document(params.text_document.uri)

    ls.analyze(
        document.uri,
        document.source,
    )


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(
    ls: RadonLanguageServer,
    params: DidChangeTextDocumentParams,
):
    document = ls.workspace.get_text_document(params.text_document.uri)

    ls.analyze(
        document.uri,
        document.source,
    )


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(
    ls: RadonLanguageServer,
    params: DidSaveTextDocumentParams,
):
    document = ls.workspace.get_text_document(params.text_document.uri)

    ls.analyze(
        document.uri,
        document.source,
    )


# ---------------------------------------------------------------------------
# Hover
# ---------------------------------------------------------------------------


@server.feature(TEXT_DOCUMENT_HOVER)
def hover(
    ls: RadonLanguageServer,
    params,
):
    return ls.get_hover(
        params.text_document.uri,
        params.position,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    logger.info("Starting Radon LSP 0.1.0")
    server.start_io()


if __name__ == "__main__":
    main()
