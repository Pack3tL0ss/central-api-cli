# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
# Add path for custom extensions
# sys.path.insert(0, os.path.abspath("./_ext"))
# path to project directory
sys.path.insert(0, os.path.abspath(".."))

# Make README the index
# index_master = True

# -- Project information -----------------------------------------------------
project = "Aruba Central API CLI (cencli)"
copyright = "2024, Wade Wells ~ Pack3tL0ss"
author = "Wade Wells ~ Pack3tL0ss"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # "sphinx_rtd_theme",
    # "sphinx_material",
    # "sphinx_book_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinxcontrib.typer",
    # "sphinx_click",
    # "richunstyle",
]
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
# html_theme = "sphinx_rtd_theme"
# html_theme = "sphinx_book_theme"
html_theme = "sphinx_material"
# html_theme = "conestack"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_show_sourcelink = False

if html_theme == "sphinx_material":
    html_sidebars = {
        "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
    }
    html_theme_options = {

        # Set the name of the project to appear in the navigation.
        'nav_title': 'Aruba Central API CLI',
        'logo_icon': '&#xe2bd;',


        # Specify a base_url used to generate sitemap.xml. If not
        # specified, then no sitemap will be built.
        # 'base_url': 'file://wsl.localhost/Ubuntu/home/wade/cencli-docs-build',

        # Set the color and the accent color
        # 'color_primary': 'deep-purple',
        # 'color_accent': 'indigo',
        'color_primary': 'blue',
        'color_accent': 'light-blue',

        # Set the repo location to get a badge with stats
        'repo_url': 'https://github.com/Pack3tL0ss/central-api-cli',
        'repo_name': 'central-api-cli',

        # Visible levels of the global TOC; -1 means unlimited
        'globaltoc_depth': 3,
        # If False, expand all TOC entries
        'globaltoc_collapse': True,
        # If True, show hidden TOC entries
        'globaltoc_includehidden': False,
    }

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True