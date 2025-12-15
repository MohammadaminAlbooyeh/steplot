"""
Python Data Structures - Main Demo
This file demonstrates the usage of all implemented data structures.
"""

from data_structures import (
    Dictionary, Stack, Queue, LinkedList, 
    List, Set, Hashtable, Tree, Graph, Tuple
)

def demo_dictionary():
    print("=" * 50)
    print("DICTIONARY DEMO")
    print("=" * 50)
    d = Dictionary()
    d['name'] = 'Alice'
    d['age'] = 30
    d['city'] = 'New York'
    print(f"Dictionary: {d}")
    print(f"Keys: {d.keys()}")
    print(f"Values: {d.values()}")
    print(f"Get 'name': {d.get('name')}")
    print(f"Contains 'age': {'age' in d}")
    del d['city']
    print(f"After deleting 'city': {d}")
    print()

def demo_stack():
    print("=" * 50)
    print("STACK DEMO")
    print("=" * 50)
    s = Stack()
    s.push(10)
    s.push(20)
    s.push(30)
    print(f"Stack: {s}")
    print(f"Peek: {s.peek()}")
    print(f"Pop: {s.pop()}")
    print(f"Stack after pop: {s}")
    print(f"Size: {s.size()}")
    print(f"Is empty: {s.is_empty()}")
    print()

def demo_queue():
    print("=" * 50)
    print("QUEUE DEMO")
    print("=" * 50)
    q = Queue()
    q.enqueue(1)
    q.enqueue(2)
    q.enqueue(3)
    print(f"Queue: {q}")
    print(f"Peek: {q.peek()}")
    print(f"Dequeue: {q.dequeue()}")
    print(f"Queue after dequeue: {q}")
    print(f"Size: {q.size()}")
    print()

def demo_linked_list():
    print("=" * 50)
    print("LINKED LIST DEMO")
    print("=" * 50)
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.prepend(0)
    print(f"Linked List: {ll}")
    ll.insert(99, 2)
    print(f"After inserting 99 at position 2: {ll}")
    print(f"Element at index 2: {ll[2]}")
    print(f"Find 99: {ll.find(99)}")
    ll.remove(99)
    print(f"After removing 99: {ll}")
    print(f"Length: {len(ll)}")
    print()

def demo_list():
    print("=" * 50)
    print("LIST DEMO")
    print("=" * 50)
    l = List()
    l.append(5)
    l.append(2)
    l.append(8)
    l.append(1)
    print(f"List: {l}")
    l.insert(1, 99)
    print(f"After inserting 99 at index 1: {l}")
    print(f"Element at index 2: {l[2]}")
    print(f"Contains 8: {8 in l}")
    l.sort()
    print(f"After sorting: {l}")
    l.reverse()
    print(f"After reversing: {l}")
    print()

def demo_set():
    print("=" * 50)
    print("SET DEMO")
    print("=" * 50)
    s1 = Set()
    s1.add(1)
    s1.add(2)
    s1.add(3)
    print(f"Set 1: {s1}")
    
    s2 = Set()
    s2.add(3)
    s2.add(4)
    s2.add(5)
    print(f"Set 2: {s2}")
    
    print(f"Union: {s1.union(s2)}")
    print(f"Intersection: {s1.intersection(s2)}")
    print(f"Difference (s1 - s2): {s1.difference(s2)}")
    print(f"Contains 2: {2 in s1}")
    print(f"Length: {len(s1)}")
    print()

def demo_hashtable():
    print("=" * 50)
    print("HASHTABLE DEMO")
    print("=" * 50)
    ht = Hashtable(size=5)
    ht['apple'] = 'red'
    ht['banana'] = 'yellow'
    ht['grape'] = 'purple'
    print(f"Hashtable: {ht}")
    print(f"Keys: {ht.keys()}")
    print(f"Values: {ht.values()}")
    print(f"Get 'apple': {ht['apple']}")
    print(f"Contains 'banana': {'banana' in ht}")
    del ht['banana']
    print(f"After deleting 'banana': {ht}")
    print()

def demo_tree():
    print("=" * 50)
    print("TREE DEMO (Binary Search Tree)")
    print("=" * 50)
    t = Tree()
    t.insert(5)
    t.insert(3)
    t.insert(7)
    t.insert(1)
    t.insert(4)
    t.insert(6)
    t.insert(9)
    print(f"Inorder traversal: {t.inorder_traversal()}")
    print(f"Preorder traversal: {t.preorder_traversal()}")
    print(f"Postorder traversal: {t.postorder_traversal()}")
    found = t.search(4)
    print(f"Search for 4: {'Found' if found else 'Not found'}")
    print()

def demo_graph():
    print("=" * 50)
    print("GRAPH DEMO")
    print("=" * 50)
    g = Graph(directed=False)
    g.add_edge('A', 'B')
    g.add_edge('A', 'C')
    g.add_edge('B', 'D')
    g.add_edge('C', 'D')
    g.add_edge('D', 'E')
    print(f"Graph: {g}")
    print(f"Neighbors of 'A': {g.get_neighbors('A')}")
    print(f"DFS from 'A': {g.dfs('A')}")
    print(f"BFS from 'A': {g.bfs('A')}")
    print()

def demo_tuple():
    print("=" * 50)
    print("TUPLE DEMO")
    print("=" * 50)
    t1 = Tuple(1, 2, 3)
    t2 = Tuple(4, 5)
    print(f"Tuple 1: {t1}")
    print(f"Tuple 2: {t2}")
    print(f"Element at index 1: {t1[1]}")
    print(f"Length: {len(t1)}")
    print(f"Contains 2: {2 in t1}")
    print(f"Index of 2: {t1.index(2)}")
    print(f"Concatenation: {t1 + t2}")
    print(f"Multiplication: {Tuple(1, 2) * 3}")
    print()

def main():
    print("\n")
    print("*" * 50)
    print("PYTHON DATA STRUCTURES DEMONSTRATION")
    print("*" * 50)
    print("\n")
    
    demo_dictionary()
    demo_stack()
    demo_queue()
    demo_linked_list()
    demo_list()
    demo_set()
    demo_hashtable()
    demo_tree()
    demo_graph()
    demo_tuple()
    
    print("*" * 50)
    print("ALL DATA STRUCTURES DEMONSTRATED SUCCESSFULLY!")
    print("*" * 50)

if __name__ == "__main__":
    main()
