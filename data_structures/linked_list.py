class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    """
    A simple singly linked list implementation.
    """

    def __init__(self):
        self.head = None
        self._size = 0

    def append(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self._size += 1

    def prepend(self, data):
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
        self._size += 1

    def insert(self, data, position):
        if position < 0 or position > self._size:
            raise IndexError("Position out of range")
        if position == 0:
            self.prepend(data)
            return
        new_node = Node(data)
        current = self.head
        for _ in range(position - 1):
            current = current.next
        new_node.next = current.next
        current.next = new_node
        self._size += 1

    def remove(self, data):
        if self.head is None:
            return
        if self.head.data == data:
            self.head = self.head.next
            self._size -= 1
            return
        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                self._size -= 1
                return
            current = current.next

    def find(self, data):
        current = self.head
        index = 0
        while current:
            if current.data == data:
                return index
            current = current.next
            index += 1
        return -1

    def __getitem__(self, index):
        if index < 0 or index >= self._size:
            raise IndexError("Index out of range")
        current = self.head
        for _ in range(index):
            current = current.next
        return current.data

    def __len__(self):
        return self._size

    def __str__(self):
        elements = []
        current = self.head
        while current:
            elements.append(str(current.data))
            current = current.next
        return "[" + " -> ".join(elements) + "]"

    def __repr__(self):
        return self.__str__()
