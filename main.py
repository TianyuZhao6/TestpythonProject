from A_star_algorithm import Graph, a_star_search, reconstruct_path

def main():
    graph = Graph()
    graph.add_edge('A', 'B', 1)
    graph.add_edge('A', 'C', 4)
    graph.add_edge('B', 'C', 1)
    graph.add_edge('B', 'D', 3)

    start = 'A'
    goal = 'D'

    came_from, cost_so_far = a_star_search(graph, start, goal)
    print(f"从{start}到{goal}的最短路径长度：", cost_so_far[goal])
    print("最短路径：", reconstruct_path(came_from, start, goal))

if __name__ == "__main__":
    main()
