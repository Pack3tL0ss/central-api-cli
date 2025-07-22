from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from rich.status import Status
from rich.console import Console

if TYPE_CHECKING:
    from rich.style import StyleType
    from rich.console import RenderableType

class Spinner(Status):
    """A Spinner Object that adds methods to rich.status.Status object

        Args:
            status (RenderableType): A status renderable (str or Text typically).
            console (Console, optional): Console instance to use, or None for global console. Defaults to None.
            spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
            spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
            speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
            refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5.
    """
    def __init__(
        self,
        status: RenderableType,
        *,
        console: Optional[Console] = None,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ):
        super().__init__(status, console=console, spinner=spinner, spinner_style=spinner_style, speed=speed, refresh_per_second=refresh_per_second)

    def fail(self, text: RenderableType = None) -> None:
        if self._live.is_started:
            self._live.stop()
        self.console.print(f":x:  {self.status}") if not text else self.console.print(f":x:  {text}")

    def succeed(self, text: RenderableType = None) -> None:
        if self._live.is_started:
            self._live.stop()
        self.console.print(f":heavy_check_mark:  {self.status}") if not text else self.console.print(f":heavy_check_mark:  {text}")

    def start(
            self,
            text: RenderableType = None,
            *,
            spinner: str = None,
            spinner_style: StyleType = None,
            speed: float = None,
        ) -> None:
        if any([text, spinner, spinner_style, speed]):
            self.update(text, spinner=spinner, spinner_style=spinner_style, speed=speed)
        if not self._live.is_started:
            self._live.start()