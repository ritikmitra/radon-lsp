from src.radon_lsp.server import RadonLanguageServer


def test_configure(server: RadonLanguageServer) -> None:

    server.configure(
        {
            "threshold": 5,
            "error_threshold": 10,
        }
    )

    assert server.settings.threshold == 5
    assert server.settings.error_threshold == 10


def test_configure_with_settings_wrapper(server: RadonLanguageServer) -> None:

    server.configure(
        {
            "settings": {
                "threshold": 5,
            }
        }
    )

    assert server.settings.threshold == 5


def test_configure_ignores_invalid_input(server: RadonLanguageServer) -> None:

    server.configure(None)

    assert server.settings.threshold == 10


def test_configure_not_instance_of_dict(server: RadonLanguageServer) -> None:

    original_settings = server.settings

    server.configure({"settings": None})

    assert server.settings is original_settings
