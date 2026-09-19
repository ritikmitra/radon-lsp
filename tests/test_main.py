import runpy
from unittest.mock import patch


def test_main_module_calls_server_main() -> None:
    with patch("radon_lsp.server.main") as mock_main:
        runpy.run_module(
            "radon_lsp.__main__",
            run_name="__main__",
        )

    mock_main.assert_called_once_with()
