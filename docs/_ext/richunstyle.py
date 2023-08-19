from sphinx.cmd.build import main
from pathlib import Path

from typing import List, Literal, Any
from rich import inspect

RICH_MARKUPS = [
    "[red]",
    "[cyan]",
    "[grey42]",
    "[green3]",
    "[reset]",
    "[italic]"
    "[bright_green]",
    ":pile_of_poo:",
    ":office:",
    "[/]"
]

def remove_rich_markup(app, domain, objtype, content):
    print("RICH UNSTYLE")
    print(type(content.document))

    # for pattern in RICH_MARKUPS:
    #     content.document = content.document.replace(pattern, "")

    # return content

def remove_rich_markup_autodoc(app, what, name, obj, options, lines):
    print(str(obj), type(obj))

def remove_rich_markup_click(app, ctx, lines):
    print(str(ctx), type(lines))


def setup(app) -> None:
    app.setup_extension('sphinx_click')
    app.add_event("sphinx-click-process-description")
    # app.connect('autodoc-process-docstring', remove_rich_markup_autodoc)
    # app.connect('object-description-transform', remove_rich_markup)
    app.connect("sphinx-click-process-description", remove_rich_markup_click)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

if __name__ == '__main__':
    docdir = Path(__file__).parent.parent
    main([str(docdir), str(docdir / "_build")] )