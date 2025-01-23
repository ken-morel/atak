"""Atak page definition."""
import pyoload

from typing import Callable
from typing import Optional


class RenderedPage:
    """renderred page."""


class Page:
    """Atak base page."""

    def render(self, args: tuple) -> RenderedPage:
        """Render the page."""
        raise NotImplementedError()

    class NotFoundError(Exception):
        """Page not found."""

        def __init__(self, url: str):
            """Not found error."""
            self.url = url


class Pager:
    """Base pager class."""

    pages: list[Page]

    def __init__(self, pages: Optional[list[Page]] = None):
        """Initialize setting the default page."""
        self.pages = pages or list()
        print(pages)

    @pyoload
    def get_page(self, url: str) -> Page:
        """Get and render the appropriate page."""
        for page in self.pages:
            if page.url == url:
                return page
        else:
            raise Page.NotFoundError(f"Page not Found {url}")
