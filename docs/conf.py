# Configuration file for the Sphinx documentation builder.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Make the package importable for autodoc (repo root is one level up).
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "LUME-WarpX"
copyright = "2026, Ryland Goldman"
author = "Ryland Goldman"
release = "1.0.0"
version = "1.0.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

# pywarpx (and several scientific deps) are not installable on Read the Docs,
# so mock them out for autodoc. WarpX must be built from source to actually run.
autodoc_mock_imports = [
    "pywarpx",
    "lume",
    "openpmd_viewer",
    "openpmd_api",
    "beamphysics",
    "pmd_beamphysics",
    "h5py",
    "scipy",
    "numpy",
    "matplotlib",
    "yaml",
]

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = "LUME-WarpX"
