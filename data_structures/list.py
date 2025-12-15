class List:
    """
    A simple dynamic array list implementation.
    """

    def __init__(self):
        self._items = []
        self._size = 0

    def append(self, item):
        self._items.append(item)
        self._size += 1

    def insert(self, index, item):
        if index < 0 or index > self._size:
            raise IndexError("Index out of range")
        self._items.insert(index, item)
        self._size += 1

    def remove(self, item):
        self._items.remove(item)
        self._size -= 1

    def pop(self, index=-1):
        if self._size == 0:
            raise IndexError("pop from empty list")
        item = self._items.pop(index)
        self._size -= 1
        return item

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        self._items[index] = value

    def __delitem__(self, index):
        del self._items[index]
        self._size -= 1

    def __len__(self):
        return self._size

    def __contains__(self, item):
        return item in self._items

    def index(self, item):
        return self._items.index(item)

    def sort(self):
        self._items.sort()

    def reverse(self):
        self._items.reverse()

    def __str__(self):
        return str(self._items)

    def __repr__(self):
        return repr(self._items)
