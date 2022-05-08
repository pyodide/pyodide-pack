from dataclasses import dataclass


@dataclass
class DynamicLib:
    """A dynamic library, shared or not.

    This class is mostly useful so we can manipulate their
    paths while preserving the initial load order.

    Examples
    --------
    >>> l = [DynamicLib('a', load_order=2), DynamicLib('b', load_order=1)]
    >>> list(sorted(l))
    [DynamicLib(path='b', load_order=1, shared=False),
     DynamicLib(path='a', load_order=2, shared=False)]
    """

    path: str
    load_order: int
    shared: bool = False

    def __lt__(self, other):
        """Implement less than to make these objects sortable"""
        return self.load_order < other.load_order
