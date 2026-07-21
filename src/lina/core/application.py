"""Application lifecycle management for Lina."""

from dataclasses import dataclass, field
from enum import Enum

from lina.core.context import ApplicationContext
from lina.core.exceptions import ApplicationLifecycleError


class ApplicationState(Enum):
    """Application lifecycle states."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"


@dataclass
class LinaApplication:
    """Minimal application lifecycle controller."""

    context: ApplicationContext
    _state: ApplicationState = field(default=ApplicationState.INITIALIZED, init=False)

    @property
    def state(self) -> ApplicationState:
        return self._state

    def start(self) -> None:
        if self._state is not ApplicationState.INITIALIZED:
            raise ApplicationLifecycleError(
                f"Cannot start application from state: {self._state.value}"
            )

        self._state = ApplicationState.RUNNING

    def stop(self) -> None:
        if self._state is not ApplicationState.RUNNING:
            raise ApplicationLifecycleError(
                f"Cannot stop application from state: {self._state.value}"
            )

        self._state = ApplicationState.STOPPED


# Stable public name used by integration checks and future entry points.  Keep
# LinaApplication for source compatibility with the existing bootstrap layer.
Application = LinaApplication
