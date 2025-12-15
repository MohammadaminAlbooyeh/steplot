class Dictionary:
    """
    A simple dictionary implementation using a hash table.
    """

    def __init__(self):
        self._table = {}

    def __setitem__(self, key, value):
        self._table[key] = value

    def __getitem__(self, key):
        return self._table[key]

    def __delitem__(self, key):
        del self._table[key]

    def __contains__(self, key):
        return key in self._table

    def __len__(self):
        return len(self._table)

    def keys(self):
        return list(self._table.keys())

    def values(self):
        return list(self._table.values())

    def items(self):
        return list(self._table.items())

    def get(self, key, default=None):
        return self._table.get(key, default)

    def pop(self, key, default=None):
        return self._table.pop(key, default)

    def clear(self):
        self._table.clear()

    def __str__(self):
        return str(self._table)

    def __repr__(self):
        return repr(self._table)
