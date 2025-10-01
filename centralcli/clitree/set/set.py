# -*- coding: utf-8 -*-
import typer

from . import firmware

app = typer.Typer()
app.add_typer(firmware.app, name="firmware")


@app.callback()
def callback():
    """
    Set Firmware Compliance
    """
    ...


if __name__ == "__main__":
    app()
