"""Configuration file for the Sphinx documentation builder."""
from dataclasses import asdict
from pathlib import Path

from sphinxawesome_theme import LinkIcon, ThemeOptions
from sphinxawesome_theme.postprocess import Icons

# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

if __name__ == "__main__":
    GH_ICON = open("./_static/github.svg").read()
else:
    GH_ICON = (Path(__file__).parent / "_static/github.svg").read_text()
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "taktk"
copyright = "2024, ken-morel"
author = "ken-morel"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinxawesome_theme"
html_static_path = ["_static"]
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
# Select theme for both light and dark mode
pygments_style = "sphinx"
# Select a different theme for dark mode
pygments_style_dark = "monokai"


html_permalinks_icon = Icons.permalinks_icon

theme_options = ThemeOptions(
    # Add your theme options. For example:
    show_breadcrumbs=True,
    main_nav_links={"About": "/about"},
    logo_dark="_static/logo.png",
    logo_light="_static/logo.png",
    breadcrumbs_separator="|",
    extra_header_link_icons={
        "github": LinkIcon(
            icon=GH_ICON, link="https://github.com/ken-morel/taktk"
        ),
    },
)

html_theme_options = asdict(theme_options)


# conf.py
# extensions.append("sphinx_docsearch")
# docsearch_app_id = "<DOCSEARCH_APP_ID>"
# docsearch_api_key = "<DOCSEARCH_SEARCH_API_KEY>"
# docsearch_index_name = "<DOCSEARCH_INDEX_NAME>"
