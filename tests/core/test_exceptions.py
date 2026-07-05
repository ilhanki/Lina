from lina.core.exceptions import (
    ApplicationLifecycleError,
    ConfigurationError,
    LinaError,
    PathResolutionError,
)


def test_core_exceptions_inherit_from_lina_error() -> None:
    assert issubclass(ConfigurationError, LinaError)
    assert issubclass(PathResolutionError, LinaError)
    assert issubclass(ApplicationLifecycleError, LinaError)


def test_lina_error_keeps_message() -> None:
    error = LinaError("Something went wrong")

    assert str(error) == "Something went wrong"


def test_specific_exceptions_keep_message() -> None:
    errors = [
        ConfigurationError("Invalid config"),
        PathResolutionError("Invalid path"),
        ApplicationLifecycleError("Invalid lifecycle state"),
    ]

    assert [str(error) for error in errors] == [
        "Invalid config",
        "Invalid path",
        "Invalid lifecycle state",
    ]

