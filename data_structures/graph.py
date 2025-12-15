from collections import defaultdict

class Graph:
    """
    A simple graph implementation using adjacency list.
    """

    def __init__(self, directed=False):
        self.adj_list = defaultdict(list)
        self.directed = directed

    def add_vertex(self, vertex):
        if vertex not in self.adj_list:
            self.adj_list[vertex] = []

    def add_edge(self, vertex1, vertex2):
        self.add_vertex(vertex1)
        self.add_vertex(vertex2)
        self.adj_list[vertex1].append(vertex2)
        if not self.directed:
            self.adj_list[vertex2].append(vertex1)

    def remove_edge(self, vertex1, vertex2):
        if vertex1 in self.adj_list and vertex2 in self.adj_list[vertex1]:
            self.adj_list[vertex1].remove(vertex2)
        if not self.directed and vertex2 in self.adj_list and vertex1 in self.adj_list[vertex2]:
            self.adj_list[vertex2].remove(vertex1)

    def get_neighbors(self, vertex):
        return self.adj_list.get(vertex, [])

    def dfs(self, start_vertex):
        visited = set()
        result = []
        self._dfs_recursive(start_vertex, visited, result)
        return result

    def _dfs_recursive(self, vertex, visited, result):
        visited.add(vertex)
        result.append(vertex)
        for neighbor in self.adj_list[vertex]:
            if neighbor not in visited:
                self._dfs_recursive(neighbor, visited, result)

    def bfs(self, start_vertex):
        visited = set()
        queue = [start_vertex]
        visited.add(start_vertex)
        result = []
        while queue:
            vertex = queue.pop(0)
            result.append(vertex)
            for neighbor in self.adj_list[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return result

    def __str__(self):
        return str(dict(self.adj_list))

    def __repr__(self):
        return self.__str__()
