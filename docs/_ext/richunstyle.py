from sphinx.cmd.build import main
from pathlib import Path
from docutils.nodes import Text

from typing import List, Literal, Any
from rich import inspect

from rich.traceback import install
install(show_locals=True)

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
RICH_INDICATORS = ["[", "]", ":"]

def remove_rich_markup(app, domain, objtype, content):
    if "cencli " not in content.source:
        return
    elif not any([pattern in str(content) for pattern in RICH_MARKUPS]):
        return

    for idx, c in enumerate(content.children):
        if all([isinstance(child, Text) for child in c.children]):
            for cidx, child in enumerate(c.children):
                newtxt = str(child)
                for pattern in RICH_MARKUPS:
                    newtxt = newtxt.replace(pattern, "")
                _parent = child.parent
                child = Text(newtxt, rawsource=newtxt)
                child.parent = _parent
                c.children[cidx] = child
            content.children[idx] = c

                # c.children = [Text(child.replace(pattern, "")) for child in c.children]
    print(f"REMOVED MARKUPS from {str(content)}")

    return content

def remove_rich_markup_autodoc(app, what, name, obj, options, lines):
    print(str(obj), type(obj))

def remove_rich_markup_click(app, ctx, lines):
    print(str(ctx), type(lines))


def setup(app) -> None:
    app.setup_extension('sphinx_click')
    # app.add_event("sphinx-click-process-description")
    app.connect('object-description-transform', remove_rich_markup)
    # app.connect('autodoc-process-docstring', remove_rich_markup_autodoc)
    # app.connect("sphinx-click-process-description", remove_rich_markup_click)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

if __name__ == '__main__':
    docdir = Path(__file__).parent.parent
    main([str(docdir), str(docdir / "_build"), "-v", "-T", "-E", "-n"] )