#!/usr/bin/env python3

from pathlib import Path

from rich.traceback import install
from sphinx.application import Sphinx

install(show_locals=True)

docs_directory = Path(__file__).parent
configuration_directory = docs_directory
source_directory = docs_directory
build_directory = docs_directory / '_build'
doctree_directory = build_directory / '.doctrees'
builder = 'html'

app = Sphinx(srcdir=source_directory, confdir=configuration_directory, outdir=build_directory, doctreedir=doctree_directory, buildername=builder)
app.build()