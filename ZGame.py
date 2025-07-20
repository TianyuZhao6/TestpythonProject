import pygame
import random
from queue import PriorityQueue

# ------------- 基础参数 -------------
GRID_SIZE = 18
CELL_SIZE = 40
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
OBSTACLES = 25
OBSTACLE_HEALTH = 12  # 可破坏障碍物初始血量
DESTRUCTIBLE_RATIO = 0.4
ZOMBIE_ATTACK = 1     # 僵尸攻击力
ITEMS = 10


# ------------- A* 图结构 -------------a
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


# ---------- 障碍物类 ----------
class Obstacle:
    def __init__(self, pos, type, hp=None):
        self.pos = pos
        self.type = type  # "Destructible" or "Indestructible"
        self.hp = hp

    def is_destroyed(self):
        return self.type == "Destructible" and self.hp <= 0


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


# --------- 随机生成障碍和初始位置及奖励 ---------
def random_obstacles_and_positions(grid_size, obstacle_count, item_count):
    positions = [(x, y) for x in range(grid_size) for y in range(grid_size)]
    # 随机选障碍物
    chosen = random.sample(positions, obstacle_count)
    destruct_count = int(obstacle_count * DESTRUCTIBLE_RATIO)
    indestruct_count = obstacle_count - destruct_count
    obstacles = set(random.sample(positions, obstacle_count))

    # 可破坏障碍物
    for p in chosen[:destruct_count]:
        obstacles[p] = Obstacle(p, "Destructible", hp=OBSTACLE_HEALTH)
    # 不可破坏障碍物
    for p in chosen[destruct_count:]:
        obstacles[p] = Obstacle(p, "Indestructible")

    # 找合法初始位置
    def pick_two_far_points(min_dist):
        empties = [p for p in positions if p not in obstacles]
        while True:
            p1, p2 = random.sample(empties, 2)
            dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
            if dist >= min_dist:
                return p1, p2

    player_pos, zombie_pos = pick_two_far_points(min_dist=5)
    # 随机生成道具，不能和障碍/起点/终点重叠
    forbidden = obstacles | {player_pos, zombie_pos}
    valid = [p for p in positions if p not in forbidden]
    items = set(random.sample(valid, item_count))
    return obstacles, items, player_pos, zombie_pos


# ---------- OO 角色定义 ----------
class Player:
    def __init__(self, pos):
        self.pos = pos

    def move(self, direction, obstacles):
        x, y = self.pos
        dx, dy = direction
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx, ny) not in obstacles:
            self.pos = (nx, ny)


class Zombie:
    def __init__(self, pos):
        self.pos = pos

    def chase(self, target_pos, graph):
        came_from, _ = a_star_search(graph, self.pos, target_pos)
        path = reconstruct_path(came_from, self.pos, target_pos)
        if len(path) > 1:
            self.pos = path[1]
        return path


# ----------- 生成格子地图 -----------
def build_graph_with_obstacles(grid_size, obstacles):
    g = Graph()
    for x in range(grid_size):
        for y in range(grid_size):
            if (x, y) in obstacles:
                continue
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < grid_size and 0 <= ny < grid_size:
                    if (nx, ny) not in obstacles:
                        g.add_edge((x, y), (nx, ny), 1)
    return g


# ------------ pygame主循环 ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    clock = pygame.time.Clock()

    # 随机生成障碍和起始点及奖励
    obstacles, items, player_start, zombie_start = random_obstacles_and_positions(GRID_SIZE, OBSTACLES,ITEMS)
    player = Player(player_start)
    zombie = Zombie(zombie_start)
    graph = build_graph_with_obstacles(GRID_SIZE, obstacles)

    running = True
    zombie_step_counter = 0
    path = []
    font = pygame.font.SysFont(None, 40)
    game_result = None  # "success" or "fail"

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 玩家移动，不能穿越障碍
        keys = pygame.key.get_pressed()
        directions = {
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0),
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
        }
        for key, dir in directions.items():
            if keys[key]:
                player.move(dir, obstacles)
                break

        # 检查拾取道具
        if player.pos in items:
            items.remove(player.pos)

        # 僵尸每5帧A*一次
        zombie_step_counter += 1
        if zombie_step_counter % 5 == 0:
            path = zombie.chase(player.pos, graph)

        # 判断是否Game Over
        if zombie.pos == player.pos:
            print("GG! Failure！")
            game_result = "fail"
            running = False

        # 判断胜利
        if not items and game_result is None:
            print("Success! Winning! ")
            game_result = "success"
            running = False

        # ------- 绘图部分 -------
        screen.fill((20, 20, 20))
        # 画网格
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, (50, 50, 50), rect, 1)
        # 奖励道具
        for ix, iy in items:
            pygame.draw.circle(screen, (255, 255, 0),
                               (ix * CELL_SIZE + CELL_SIZE // 2, iy * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 3)
        pygame.draw.rect(screen, (0, 255, 0),
                         (player.pos[0] * CELL_SIZE, player.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(screen, (255, 60, 60),
                         (zombie.pos[0] * CELL_SIZE, zombie.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        # 画障碍
        for ox, oy in obstacles:
            pygame.draw.rect(screen, (120, 120, 120), (ox * CELL_SIZE, oy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (0, 255, 0),
                             (player.pos[0] * CELL_SIZE, player.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (255, 60, 60),
                             (zombie.pos[0] * CELL_SIZE, zombie.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        # 路径可视化
        # for p in path[1:]:
        #     pygame.draw.circle(screen, (0, 255, 255),
        #                        (p[0] * CELL_SIZE + CELL_SIZE // 2, p[1] * CELL_SIZE + CELL_SIZE // 2), 8)

        pygame.display.flip()
        clock.tick(15)
    # 显示结果
    screen.fill((0, 0, 0))
    if game_result == "success":
        txt = font.render("SUCCESS! All items collected!", True, (0, 255, 0))
    else:
        txt = font.render("GAME OVER! Caught by zombie ", True, (255, 60, 60))
    screen.blit(txt, (40, WINDOW_SIZE // 2 - 30))
    pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()


if __name__ == "__main__":
    main()
