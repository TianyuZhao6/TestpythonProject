import pygame
from queue import PriorityQueue

# ------------- 基础参数 -------------
GRID_SIZE = 10
CELL_SIZE = 40
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
OBSTACLES = {(3, 3), (3, 4), (3, 5), (5, 6), (5, 7)}  # 随便设置几个障碍

# ------------- A* 图结构 -------------
class Graph:
    def __init__(self):
        self.edges = {}
        self.weights = {}

    def add_edge(self, from_node, to_node, weight):
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        self.weights[(from_node, to_node)] = weight

    def neighbors(self, node):
        return self.edges.get(node, [])

    def cost(self, from_node, to_node):
        return self.weights.get((from_node, to_node), float('inf'))

def heuristic(a, b):
    # 曼哈顿距离，适合格子图
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(graph, start, goal):
    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while not frontier.empty():
        _, current = frontier.get()
        if current == goal:
            break
        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put((priority, next))
                came_from[next] = current
    return came_from, cost_so_far

def reconstruct_path(came_from, start, goal):
    if goal not in came_from:
        return [start]
    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path

# ----------- 生成格子地图 -----------
def build_graph_with_obstacles(grid_size, obstacles):
    g = Graph()
    for x in range(grid_size):
        for y in range(grid_size):
            if (x, y) in obstacles:
                continue
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < grid_size and 0 <= ny < grid_size:
                    if (nx, ny) not in obstacles:
                        g.add_edge((x, y), (nx, ny), 1)
    return g

# ------------ pygame主循环 ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    clock = pygame.time.Clock()

    player_pos = (0, 0)
    zombie_pos = (GRID_SIZE - 1, GRID_SIZE - 1)

    graph = build_graph_with_obstacles(GRID_SIZE, OBSTACLES)

    running = True
    zombie_step_counter = 0
    path = []

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 玩家移动，不能穿越障碍
        keys = pygame.key.get_pressed()
        px, py = player_pos
        for dx, dy, key in [(-1,0,pygame.K_LEFT), (1,0,pygame.K_RIGHT), (0,-1,pygame.K_UP), (0,1,pygame.K_DOWN)]:
            if keys[key]:
                nx, ny = px + dx, py + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx, ny) not in OBSTACLES:
                    player_pos = (nx, ny)
                    break

        # 僵尸每5帧A*一次
        zombie_step_counter += 1
        if zombie_step_counter % 5 == 0:
            came_from, _ = a_star_search(graph, zombie_pos, player_pos)
            path = reconstruct_path(came_from, zombie_pos, player_pos)
