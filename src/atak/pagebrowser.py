"""Page browsing utility."""
import pyoload

from typing import Any
from typing import Optional

Page = Any
StackEntry = tuple[str, Page]


@pyoload(
    validators=dict(
        index=lambda idx: "Page stack index can only be positive."
        if idx < 0
        else None
    )
)
class PageBrowser:
    """Page Browser class."""

    stack: list[StackEntry]
    index: int
    page_changed: bool

    def __init__(self):
        """Create the browser."""
        self.stack = list()
        self.index = 0
        self.page_changed = False

    def get_current(self) -> Optional[StackEntry]:
        """Get the current page to be viewed."""
        if len(self.stack) == 0:
            return None
        return self.stack[self.index]

    def back(self) -> Optional[StackEntry]:
        """Go back in history."""
        if self.index > 1:
            self.index -= 1
        return self.get_current()

    def set_page(self, page: StackEntry) -> StackEntry:
        """Replace the current page entry in hierarchy."""
        if self.index >= len(self.stack):
            self.index = len(self.stack)
            self.stack.append(page)
        else:
            self.stack[self.index] = page
        return page

    def next_page(self, page: StackEntry) -> StackEntry:
        """Stack the page entry in hierarchy."""
        self.index = len(self.stack)
        self.stack.append(page)
        return page
