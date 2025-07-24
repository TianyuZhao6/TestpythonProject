import pygame
import math
import random
from queue import PriorityQueue

# ------------- 基础参数 -------------

GRID_SIZE = 18
CELL_SIZE = 40
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
OBSTACLES = 25
OBSTACLE_HEALTH = 20  # 可破坏障碍物初始血量
DESTRUCTIBLE_RATIO = 0.4
PLAY_SPEED = 2
ZOMBIE_SPEED = 5
ZOMBIE_ATTACK = 10  # 僵尸攻击力
ZOMBIE_NUM = 2
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


# ---------- OO 角色定义 ----------
class Player:
    def __init__(self, pos, speed=PLAY_SPEED):
        self.pos = pos
        self.speed = speed
        self.move_cooldown = 0

    def move(self, direction, obstacles):
        if self.move_cooldown <= 0:
            x, y = self.pos
            dx, dy = direction
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx, ny) not in obstacles:
                self.pos = (nx, ny)
                self.move_cooldown = self.speed


class Zombie:
    def __init__(self, pos, attack=ZOMBIE_ATTACK, speed=ZOMBIE_SPEED):
        self.pos = pos
        self.attack = attack
        self.speed = speed
        self.move_cooldown = random.randint(0, speed-1)  # 让僵尸不完全同步
        self.breaking_obstacle = None

    def chase(self, target_pos, graph, obstacles):
        came_from, _ = a_star_search(graph, self.pos, target_pos, obstacles)
        path = reconstruct_path(came_from, self.pos, target_pos)
        if len(path) > 1:
            next_pos = path[1]
            # 如果下一个位置是可破坏障碍物
            if next_pos in obstacles and obstacles[next_pos].type == "Destructible":
                # 攻击障碍
                obstacles[next_pos].hp -= ZOMBIE_ATTACK
                # 如果障碍hp <= 0，移除障碍
                if obstacles[next_pos].hp <= 0:
                    del obstacles[next_pos]
                    # 重新构建graph
                    return "destroy", next_pos
                else:
                    return "attack", next_pos

            elif next_pos not in obstacles:
                self.pos = next_pos
                self.breaking_obstacle = None
                return "move", next_pos

        return "idle", self.pos


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


def a_star_search(graph, start, goal, obstacles):
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
            if next in obstacles:
                obs = obstacles[next]
                if obs.type == "Indestructible":
                    continue  # 不能扩展
                elif obs.type == "Destructible":
                    K = (math.ceil(obs.hp / ZOMBIE_ATTACK)) * 0.1
                    new_cost = cost_so_far[current] + 1 + K
                else:
                    new_cost = cost_so_far[current] + 1
            else:
                new_cost = cost_so_far[current] + 1
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
def random_obstacles_and_positions(grid_size, obstacle_count, item_count, zombie_num):
    positions = [(x, y) for x in range(grid_size) for y in range(grid_size)]
    # 随机选障碍物
    chosen = random.sample(positions, obstacle_count)
    destruct_count = int(obstacle_count * DESTRUCTIBLE_RATIO)
    # indestruct_count = obstacle_count - destruct_count
    obstacles = dict()

    # 可破坏障碍物
    for p in chosen[:destruct_count]:
        obstacles[p] = Obstacle(p, "Destructible", hp=OBSTACLE_HEALTH)
    # 不可破坏障碍物
    for p in chosen[destruct_count:]:
        obstacles[p] = Obstacle(p, "Indestructible")

    # 找合法初始位置
    def pick_positions(min_dist, count):
        empties = [p for p in positions if p not in obstacles]
        while True:
            picks = random.sample(empties, count + 1)
            player_pos = picks[0]
            zombie_poses = picks[1:]
            if all(abs(player_pos[0] - z[0]) + abs(player_pos[1] - z[1]) >= min_dist for z in zombie_poses):
                return player_pos, zombie_poses

    player_pos, zombie_poses = pick_positions(min_dist=5, count=zombie_num)
    # 随机生成道具，不能和障碍/起点/终点重叠
    forbidden = set(obstacles) | {player_pos} | set(zombie_poses)
    valid = [p for p in positions if p not in forbidden]
    items = set(random.sample(valid, item_count))
    return obstacles, items, player_pos, zombie_poses


# ----------- 生成格子地图 -----------
def build_graph_with_obstacles(grid_size, obstacles):
    g = Graph()
    for x in range(grid_size):
        for y in range(grid_size):
            # 跳过不可破坏障碍物
            if (x, y) in obstacles and obstacles[(x, y)].type == "Indestructible":
                continue

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < grid_size and 0 <= ny < grid_size:
                    # 跳过不可破坏障碍物
                    if (nx, ny) in obstacles and obstacles[(nx, ny)].type == "Indestructible":
                        continue

                    # 添加边并设置权重
                    weight = 1

                    # 如果是可破坏障碍物，增加权重
                    if (nx, ny) in obstacles and obstacles[(nx, ny)].type == "Destructible":
                        # 显著增加破坏障碍物的代价，确保优先选择破坏
                        weight = 10  # 基础代价

                    g.add_edge((x, y), (nx, ny), weight)
    return g


# ------------ pygame主循环 ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    clock = pygame.time.Clock()

    # 随机生成障碍和起始点及奖励
    obstacles, items, player_start, zombie_starts = random_obstacles_and_positions(GRID_SIZE, OBSTACLES, ITEMS, ZOMBIE_NUM)
    player = Player(player_start, speed=PLAY_SPEED)
    zombies = [Zombie(z, speed=ZOMBIE_SPEED) for z in zombie_starts]
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
        if player.move_cooldown > 0:
            player.move_cooldown -= 1
        for key, dir in directions.items():
            if keys[key]:
                player.move(dir, obstacles)
                break

        # 检查拾取道具
        if player.pos in items:
            items.remove(player.pos)

        # 僵尸移动
        for zombie in zombies:
            if zombie.move_cooldown > 0:
                zombie.move_cooldown -= 1
                continue
            action, pos = zombie.chase(player.pos, graph, obstacles)
            if action == "destroy":
                graph = build_graph_with_obstacles(GRID_SIZE, obstacles)
            if action == "move":
                zombie.pos = pos
            zombie.move_cooldown = zombie.speed  # 移动后重置
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
        # 绘制所有僵尸
        for zombie in zombies:
            pygame.draw.rect(screen, (255, 60, 60),
                             (zombie.pos[0] * CELL_SIZE, zombie.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        # 画障碍
        for ox, oy in obstacles:
            pygame.draw.rect(screen, (120, 120, 120), (ox * CELL_SIZE, oy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (0, 255, 0),
                             (player.pos[0] * CELL_SIZE, player.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (255, 60, 60),
                             (zombie.pos[0] * CELL_SIZE, zombie.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        for obs in obstacles.values():
            color = (200, 80, 80) if obs.type == "Destructible" else (120, 120, 120)
            pygame.draw.rect(screen, color, (obs.pos[0] * CELL_SIZE, obs.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            if obs.type == "Destructible":
                hp_text = font.render(str(obs.hp), True, (255, 255, 255))
                screen.blit(hp_text, (obs.pos[0] * CELL_SIZE + 6, obs.pos[1] * CELL_SIZE + 8))

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
    pygame.time.wait(1500)
    pygame.quit()


if __name__ == "__main__":
    main()

# TODO
#  ADDING MULTIPLE TYPE/ NUMBER OF MONSTER AGAINST PLAYER  DONE
#  Possibly increase player ability/ Balancing the speed of Zombies & Player
#  Adding more interaction with the blocks and other feature on map
#  Adding multiple chapters after completing single one
