# -*- coding: utf-8 -*-
# WiP not used yet.  Consistent def for all Arguments / Options

from typing import Optional, Annotated

import typer

class CLIOptions:
    def __init__(self,):
        self.yes: Annotated[Optional[bool], typer.Option("-Y", help="Bypass confirmation prompts - Assume Yes")] = False,
        self.debug: Annotated[Optional[bool], typer.Option("--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",)] = False,