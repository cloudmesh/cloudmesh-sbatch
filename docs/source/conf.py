# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sphinx_rtd_theme
import os
import sys
import cloudmesh.sbatch
from cloudmesh.sbatch.__version__ import version as cc_version

rtd = True
# rtd = False

sys.path.insert(0, os.path.abspath('..'))
# sys.path.insert(0, os.path.abspath('../../cloudmesh'))


numfig = True


html_theme = "sphinx_rtd_theme"


project = 'cloudmesh-sbatch'
copyright = '2022, Gregor von Laszewski'
author = 'Gregor von Laszewski'
release = cc_version



extensions = []
extensions.append('sphinx_rtd_theme')
extensions.append('sphinx.ext.todo')
extensions.append('sphinx.ext.autodoc')
extensions.append('sphinx.ext.autosummary')
extensions.append('sphinx.ext.intersphinx')
extensions.append('sphinx.ext.mathjax')
extensions.append('sphinx.ext.viewcode')
extensions.append('sphinx.ext.graphviz')
extensions.append('sphinx_autodoc_typehints')
extensions.append('myst_parser')
extensions.append('sphinxcontrib.openapi')
# extensions.append('sphinxcontrib.fulltoc')
extensions.append('sphinx_copybutton')

#extensions.append('sphinx.ext.githubpages')
#extensions.append('sphinx.ext.napoleon')
#extensions.append('sphinx.ext.todo')


numfig=True
autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = True  # Remove 'view source code' from top of page (for html, not python)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
nbsphinx_allow_errors = True  # Continue through Jupyter errors
#autodoc_typehints = "description" # Sphinx-native method. Not as good as sphinx_autodoc_typehints
add_module_names = False # Remove namespaces from class/method signatures

# replace "view page source" with "edit on github" in Read The Docs theme
#  * https://github.com/readthedocs/sphinx_rtd_theme/issues/529
html_context = {
  'display_github': True,
  'github_user': 'cloudmesh',
  'github_repo': 'cloudmesh-cc',
  'github_version': 'main/api/source/',
}
templates_path = ['_templates']
exclude_patterns = []

source_suffix = ['.rst', '.md']
todo_include_todos = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


# Readthedocs theme
# on_rtd is whether on readthedocs.org, this line of code grabbed from docs.readthedocs.org...
on_rtd = os.environ.get("READTHEDOCS", None) == "True"
if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_css_files = ["readthedocs-custom.css"] # Override some CSS settings
html_static_path = ['_static']

# html_theme = 'sphinx_rtd_theme'
# html_static_path = ['_static']

autosummary_generate = True
# html_theme = 'default'
if not rtd:
    html_theme = 'sphinx_material'
    html_sidebars = {
        "**": [# "logo-text.html",
               "searchbox.html",
               "globaltoc.html",
               "localtoc.html",
               "genindex.html",
               "generated/cloudmesh.cc.html"]}
    html_theme_options = {
        'repo_url': 'https://github.com/cloudmesh/cloudmesh-cc'
    }
else:
    html_sidebars = { '**': [
        'globaltoc.html',
        'relations.html',
        'sourcelink.html',
        'searchbox.html'] }




