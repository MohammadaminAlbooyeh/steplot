# Python Data Structures

A comprehensive collection of data structure implementations in Python, built from scratch using only the standard library. This project serves as both an educational resource and a reusable library for common data structures.

## Features

- **Educational**: Each data structure is implemented from scratch to demonstrate core concepts
- **Standard Library Only**: No external dependencies required
- **Comprehensive**: Includes 10 different data structures with full functionality
- **Well-Documented**: Each class includes docstrings and usage examples
- **Tested**: Includes a demo file (`main.py`) that showcases all implementations

## Requirements

- Python 3.6+
- No external dependencies (uses only Python standard library)

## Data Structures Implemented

### 1. Dictionary
A hash table-based dictionary implementation with key-value storage.
- **Methods**: `__setitem__`, `__getitem__`, `__delitem__`, `keys()`, `values()`, `items()`, `get()`, `pop()`, `clear()`
- **Time Complexity**: O(1) average case for all operations

### 2. Stack
Last-In-First-Out (LIFO) data structure.
- **Methods**: `push()`, `pop()`, `peek()`, `is_empty()`, `size()`
- **Time Complexity**: O(1) for all operations

### 3. Queue
First-In-First-Out (FIFO) data structure.
- **Methods**: `enqueue()`, `dequeue()`, `peek()`, `is_empty()`, `size()`
- **Time Complexity**: O(1) for all operations

### 4. Linked List
Singly linked list implementation.
- **Methods**: `append()`, `prepend()`, `insert()`, `remove()`, `find()`, `__getitem__()`, `__len__()`
- **Time Complexity**: O(1) for append/prepend, O(n) for insert/remove/find

### 5. List
Dynamic array-based list implementation.
- **Methods**: `append()`, `insert()`, `remove()`, `pop()`, `__getitem__()`, `__setitem__()`, `__delitem__()`, `index()`, `sort()`, `reverse()`
- **Time Complexity**: O(1) for append, O(n) for insert/remove/search

### 6. Set
Hash-based set implementation with unique elements.
- **Methods**: `add()`, `remove()`, `discard()`, `union()`, `intersection()`, `difference()`, `clear()`
- **Time Complexity**: O(1) average case for add/remove/contains

### 7. Hashtable
Custom hash table with separate chaining collision resolution.
- **Methods**: `__setitem__`, `__getitem__`, `__delitem__`, `keys()`, `values()`, `items()`, `__len__()`
- **Time Complexity**: O(1) average case, O(n) worst case

### 8. Tree
Binary search tree implementation.
- **Methods**: `insert()`, `search()`, `inorder_traversal()`, `preorder_traversal()`, `postorder_traversal()`
- **Time Complexity**: O(log n) average case for insert/search, O(n) for traversals

### 9. Graph
Adjacency list-based graph with DFS and BFS traversal.
- **Methods**: `add_vertex()`, `add_edge()`, `remove_edge()`, `get_neighbors()`, `dfs()`, `bfs()`
- **Time Complexity**: O(1) for add_edge, O(V+E) for traversals

### 10. Tuple
Immutable sequence implementation.
- **Methods**: `__getitem__()`, `__len__()`, `__contains__()`, `index()`, `count()`, `__add__()`, `__mul__()`
- **Time Complexity**: O(1) for access, O(n) for search operations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MohammadaminAlbooyeh/python_data_structure.git
cd python_data_structure
```

2. No additional setup required - uses only Python standard library.

## Usage

### Import and Use Data Structures

```python
from data_structures import Dictionary, Stack, Queue

# Dictionary example
d = Dictionary()
d['key'] = 'value'
print(d['key'])  # Output: value

# Stack example
s = Stack()
s.push(1)
s.push(2)
print(s.pop())  # Output: 2

# Queue example
q = Queue()
q.enqueue(1)
q.enqueue(2)
print(q.dequeue())  # Output: 1
```

### Run the Demo

Execute the demo file to see all data structures in action:

```bash
python main.py
```

This will run comprehensive demonstrations of each data structure with example usage and output.

## Testing

Run the demo to verify all implementations:

```bash
python main.py
```

The demo includes test cases for each data structure to ensure correctness.

## Project Structure

```
python_data_structure/
├── README.md                 # This file
├── main.py                   # Demo and testing file
└── data_structures/          # Package directory
    ├── __init__.py          # Package initialization and imports
    ├── dictionary.py        # Dictionary implementation
    ├── stack.py             # Stack implementation
    ├── queue.py             # Queue implementation
    ├── linked_list.py       # Linked list implementation
    ├── list.py              # Dynamic list implementation
    ├── set.py               # Set implementation
    ├── hashtable.py         # Hash table implementation
    ├── tree.py              # Binary search tree implementation
    ├── graph.py             # Graph implementation
    └── tuple.py             # Tuple implementation
```

## Learning Objectives

This project demonstrates:
- Object-oriented programming principles
- Data structure design patterns
- Time complexity analysis
- Memory management concepts
- Algorithm implementation
- Python class design and special methods

## Contributing

Feel free to contribute by:
- Reporting bugs
- Suggesting new features
- Improving documentation
- Adding more data structures
- Optimizing implementations

## License

This project is open source and available under the MIT License.
