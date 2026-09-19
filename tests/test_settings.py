from src.radon_lsp.server import RadonSettings


def test_default_settings() -> None:
    settings = RadonSettings.from_dict(None)

    assert settings.threshold == 10
    assert settings.error_threshold == 20
    assert settings.enable_complexity is True
    assert settings.enable_maintainability is True
    assert settings.maintainability_threshold == 65.0
    assert settings.maintainability_error_threshold == 50.0
    assert settings.show_grade is True


def test_custom_settings():
    settings = RadonSettings.from_dict(
        {
            "threshold": 5,
            "error_threshold": 15,
            "enable_complexity": False,
            "enable_maintainability": False,
            "maintainability_threshold": 70,
            "maintainability_error_threshold": 40,
            "show_grade": False,
        }
    )

    assert settings.threshold == 5
    assert settings.error_threshold == 15
    assert settings.enable_complexity is False
    assert settings.enable_maintainability is False
    assert settings.maintainability_threshold == 70.0
    assert settings.maintainability_error_threshold == 40.0
    assert settings.show_grade is False


def test_invalid_integer_uses_default():
    settings = RadonSettings.from_dict(
        {
            "threshold": "not-a-number",
        }
    )

    assert settings.threshold == 10


def test_invalid_float_uses_default():
    settings = RadonSettings.from_dict(
        {
            "maintainability_threshold": "invalid",
        }
    )

    assert settings.maintainability_threshold == 65.0


def test_invalid_boolean_uses_default():
    settings = RadonSettings.from_dict(
        {
            "show_grade": "false",
        }
    )

    assert settings.show_grade is True


