class Hashtable:
    """
    A simple hash table implementation using separate chaining.
    """

    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(size)]

    def _hash(self, key):
        return hash(key) % self.size

    def __setitem__(self, key, value):
        index = self._hash(key)
        for i, (k, v) in enumerate(self.table[index]):
            if k == key:
                self.table[index][i] = (key, value)
                return
        self.table[index].append((key, value))

    def __getitem__(self, key):
        index = self._hash(key)
        for k, v in self.table[index]:
            if k == key:
                return v
        raise KeyError(key)

    def __delitem__(self, key):
        index = self._hash(key)
        for i, (k, v) in enumerate(self.table[index]):
            if k == key:
                del self.table[index][i]
                return
        raise KeyError(key)

    def __contains__(self, key):
        index = self._hash(key)
        for k, v in self.table[index]:
            if k == key:
                return True
        return False

    def keys(self):
        keys = []
        for bucket in self.table:
            for k, v in bucket:
                keys.append(k)
        return keys

    def values(self):
        values = []
        for bucket in self.table:
            for k, v in bucket:
                values.append(v)
        return values

    def items(self):
        items = []
        for bucket in self.table:
            items.extend(bucket)
        return items

    def __len__(self):
        return sum(len(bucket) for bucket in self.table)

    def __str__(self):
        return str(dict(self.items()))

    def __repr__(self):
        return repr(dict(self.items()))
