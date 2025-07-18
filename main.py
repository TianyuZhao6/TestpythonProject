from A_star_algorithm import Graph, a_star_search, reconstruct_path

def main():
    # graph = Graph()
    # graph.add_edge('A', 'B', 1)
    # graph.add_edge('A', 'C', 4)
    # graph.add_edge('B', 'C', 1)
    # graph.add_edge('B', 'D', 3)
    #
    # start = 'A'
    # goal = 'D'
    graph = Graph()
    # 生成一个网格状的图：四个点，坐标为(0,0), (1,0), (0,1), (1,1)
    nodes = [(0, 0), (1, 0), (0, 1), (1, 1)]
    # 手动连线，权重用曼哈顿距离
    graph.add_edge((0, 0), (1, 0), 1)
    graph.add_edge((0, 0), (0, 1), 1)
    graph.add_edge((1, 0), (1, 1), 1)
    graph.add_edge((0, 1), (1, 1), 1)

    start = (0, 0)
    goal = (1, 1)

    came_from, cost_so_far = a_star_search(graph, start, goal)
    print(f"从{start}到{goal}的最短路径长度：", cost_so_far[goal])
    print("最短路径：", reconstruct_path(came_from, start, goal))

if __name__ == "__main__":
    main()
