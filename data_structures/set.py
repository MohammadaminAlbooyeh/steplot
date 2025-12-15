class Set:
    """
    A simple set implementation using a dictionary.
    """

    def __init__(self):
        self._items = {}

    def add(self, item):
        self._items[item] = True

    def remove(self, item):
        if item not in self._items:
            raise KeyError(item)
        del self._items[item]

    def discard(self, item):
        if item in self._items:
            del self._items[item]

    def __contains__(self, item):
        return item in self._items

    def __len__(self):
        return len(self._items)

    def clear(self):
        self._items.clear()

    def union(self, other):
        result = Set()
        for item in self._items:
            result.add(item)
        for item in other._items:
            result.add(item)
        return result

    def intersection(self, other):
        result = Set()
        for item in self._items:
            if item in other:
                result.add(item)
        return result

    def difference(self, other):
        result = Set()
        for item in self._items:
            if item not in other:
                result.add(item)
        return result

    def __str__(self):
        return "{" + ", ".join(str(item) for item in self._items) + "}"

    def __repr__(self):
        return self.__str__()
