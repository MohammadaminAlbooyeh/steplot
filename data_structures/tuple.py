class Tuple:
    """
    A simple tuple implementation (immutable sequence).
    """

    def __init__(self, *args):
        self._items = list(args)

    def __getitem__(self, index):
        return self._items[index]

    def __len__(self):
        return len(self._items)

    def __contains__(self, item):
        return item in self._items

    def index(self, item):
        return self._items.index(item)

    def count(self, item):
        return self._items.count(item)

    def __add__(self, other):
        if isinstance(other, Tuple):
            return Tuple(*self._items, *other._items)
        return NotImplemented

    def __mul__(self, n):
        return Tuple(*self._items * n)

    def __str__(self):
        return "(" + ", ".join(str(item) for item in self._items) + ")"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Tuple):
            return self._items == other._items
        return False

    def __hash__(self):
        return hash(tuple(self._items))
