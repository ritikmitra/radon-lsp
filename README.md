# radon-lsp

[![CI](https://github.com/ritikmitra/radon-lsp/actions/workflows/ci.yml/badge.svg)](https://github.com/ritikmitra/radon-lsp/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/gh/ritikmitra/radon-lsp/graph/badge.svg)](https://app.codecov.io/gh/ritikmitra/radon-lsp)
[![Release](https://img.shields.io/github/v/release/ritikmitra/radon-lsp)](https://github.com/ritikmitra/radon-lsp/releases)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/github/license/ritikmitra/radon-lsp)](https://github.com/ritikmitra/radon-lsp/blob/main/LICENSE)

A lightweight Python Language Server Protocol (LSP) implementation that brings
[Radon](https://radon.readthedocs.io/) code-quality metrics directly into your
editor.

`radon-lsp` analyzes Python source code and reports code-quality issues as
standard LSP diagnostics, making complexity and maintainability problems
visible directly in your editor.

## Features

- 🔍 **Cyclomatic complexity** — detect overly complex functions and methods
- 📊 **Radon complexity grades** — display grades such as `A`, `B`, `C`, etc.
- 🧹 **Maintainability Index** — identify code with low maintainability
- ⚠️ **Configurable thresholds** — control warning and error levels
- 💬 **LSP diagnostics** — problems appear directly in your editor
- 💡 **Hover information** — inspect complexity and maintainability metrics
- ⚙️ **Editor configuration** — configure analysis behavior through LSP settings
- 🖥️ **Cross-platform builds** — Windows, macOS, and Linux releases
- 🚀 **Automated releases** — GitHub Releases are generated from version tags
- 🔒 **Dependency auditing** — CI checks dependencies with `pip-audit`
- 📈 **Code coverage** — test coverage is tracked with Codecov

## CI & Quality

Every push and pull request runs the project's automated quality checks.

The CI pipeline currently performs:

- Test suite execution with `pytest`
- Code coverage generation
- Codecov coverage reporting
- Dependency vulnerability auditing with `pip-audit`

Release tags automatically trigger cross-platform builds for Windows, macOS,
and Linux.

## Development

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

Install the development environment:

```bash
uv sync --dev
```