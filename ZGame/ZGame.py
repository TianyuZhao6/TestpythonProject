import pygame
import math
import random
from queue import PriorityQueue
from typing import Dict, List, Set, Tuple, Optional

# ==================== 游戏常量配置 ====================

GRID_SIZE = 18
CELL_SIZE = 40
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
OBSTACLES = 25
OBSTACLE_HEALTH = 20  # 可破坏障碍物初始血量
DESTRUCTIBLE_RATIO = 0.3
PLAYER_SPEED = 2
ZOMBIE_SPEED = 5
ZOMBIE_ATTACK = 10  # 僵尸攻击力
ZOMBIE_NUM = 2
ITEMS = 10
# LOCKED_ITEM_COLOR = (0, 100, 255)  # 锁定的特殊物品颜色
# UNLOCKED_ITEM_COLOR = (255, 200, 0)  # 解锁后的颜色

# 方向向量
DIRECTIONS = {
    pygame.K_a: (-1, 0),  # 左
    pygame.K_d: (1, 0),  # 右
    pygame.K_w: (0, -1),  # 上
    pygame.K_s: (0, 1),  # 下
}


# ==================== 数据结构 ====================
class Graph:
    """表示游戏地图的图结构，用于路径查找"""

    def __init__(self):
        self.edges: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        self.weights: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float] = {}

    def add_edge(self, from_node: Tuple[int, int], to_node: Tuple[int, int], weight: float) -> None:
        """添加一条边到图中"""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        self.weights[(from_node, to_node)] = weight

    def neighbors(self, node: Tuple[int, int]) -> List[Tuple[int, int]]:
        """获取节点的邻居"""
        return self.edges.get(node, [])

    def cost(self, from_node: Tuple[int, int], to_node: Tuple[int, int]) -> float:
        """获取两个节点之间的移动代价"""
        return self.weights.get((from_node, to_node), float('inf'))


class Obstacle:
    """表示游戏中的障碍物"""

    def __init__(self, pos: Tuple[int, int], obstacle_type: str, health: Optional[int] = None):
        """
        初始化障碍物

        Args:
            pos: 障碍物位置 (x, y)
            obstacle_type: 障碍物类型 ("Destructible" 或 "Indestructible")
            health: 可破坏障碍物的生命值 (仅对可破坏障碍物有效)
        """
        self.pos: Tuple[int, int] = pos
        self.type: str = obstacle_type
        self.health: Optional[int] = health

    def is_destroyed(self) -> bool:
        """检查障碍物是否已被破坏"""
        return self.type == "Destructible" and self.health <= 0


# ---------- OO 角色定义 ----------
class Player:
    """玩家角色"""

    def __init__(self, pos: Tuple[int, int], speed: int = PLAYER_SPEED):
        """
        初始化玩家

        Args:
            pos: 初始位置 (x, y)
            speed: 移动速度 (值越大移动越慢)
        """
        self.pos: Tuple[int, int] = pos
        self.speed: int = speed
        self.move_cooldown: int = 0

    def move(self, direction: Tuple[int, int], obstacles: Dict[Tuple[int, int], Obstacle]) -> None:
        """在指定方向上移动玩家

        Args:
            direction: 移动方向 (dx, dy)
            obstacles: 障碍物字典
        """
        if self.move_cooldown <= 0:
            x, y = self.pos
            dx, dy = direction
            new_x, new_y = x + dx, y + dy

            # 检查新位置是否有效
            if (0 <= new_x < GRID_SIZE and
                    0 <= new_y < GRID_SIZE and
                    (new_x, new_y) not in obstacles):
                self.pos = (new_x, new_y)
                self.move_cooldown = self.speed


class Zombie:
    """僵尸角色"""

    def __init__(self, pos: Tuple[int, int], attack: int = ZOMBIE_ATTACK, speed: int = ZOMBIE_SPEED):
        """
        初始化僵尸

        Args:
            pos: 初始位置 (x, y)
            attack: 攻击力
            speed: 移动速度 (值越大移动越慢)
        """
        self.pos: Tuple[int, int] = pos
        self.attack: int = attack
        self.speed: int = speed
        self.move_cooldown: int = random.randint(0, speed - 1)  # 让僵尸移动不完全同步
        self.breaking_obstacle: Optional[Tuple[int, int]] = None

    def chase(self, target_pos: Tuple[int, int], graph: Graph,
              obstacles: Dict[Tuple[int, int], Obstacle]) -> Tuple[str, Tuple[int, int]]:
        """
        追逐目标位置

        Args:
            target_pos: 目标位置 (玩家位置)
            graph: 地图图结构
            obstacles: 障碍物字典

        Returns:
            (动作类型, 目标位置)
        """
        # 使用A*算法查找路径
        came_from, _ = a_star_search(graph, self.pos, target_pos, obstacles)
        path = reconstruct_path(came_from, self.pos, target_pos)

        if len(path) > 1:
            next_pos = path[1]

            # 如果下一个位置是可破坏障碍物
            if next_pos in obstacles and obstacles[next_pos].type == "Destructible":
                # 攻击障碍物
                obstacles[next_pos].health -= self.attack

                # 检查障碍物是否被破坏
                if obstacles[next_pos].health <= 0:
                    del obstacles[next_pos]
                    return "destroy", next_pos
                else:
                    return "attack", next_pos

            # 如果下一个位置可通行
            elif next_pos not in obstacles:
                self.pos = next_pos
                self.breaking_obstacle = None
                return "move", next_pos

        return "idle", self.pos


# ==================== 算法函数 ====================
def heuristic(a, b):
    # 曼哈顿距离，适合格子图
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star_search(graph: Graph, start: Tuple[int, int], goal: Tuple[int, int],
                  obstacles: Dict[Tuple[int, int], Obstacle]) -> Tuple[Dict, Dict]:
    """
    A*寻路算法实现

    Args:
        graph: 地图图结构
        start: 起始位置
        goal: 目标位置
        obstacles: 障碍物字典

    Returns:
        (路径字典, 代价字典)
    """
    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while not frontier.empty():
        _, current = frontier.get()

        # 找到目标位置，结束搜索
        if current == goal:
            break

        # 探索邻居节点
        for neighbor in graph.neighbors(current):
            # 计算新代价
            new_cost = cost_so_far[current] + graph.cost(current, neighbor)

            # 处理障碍物
            if neighbor in obstacles:
                obstacle = obstacles[neighbor]

                # 不可破坏障碍物，跳过
                if obstacle.type == "Indestructible":
                    continue

                # 可破坏障碍物，增加额外代价
                elif obstacle.type == "Destructible":
                    # 计算破坏障碍物所需的额外代价
                    k_factor = (math.ceil(obstacle.health / ZOMBIE_ATTACK)) * 0.1
                    new_cost = cost_so_far[current] + 1 + k_factor

            # 更新节点代价
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(goal, neighbor)
                frontier.put((priority, neighbor))
                came_from[neighbor] = current

    return came_from, cost_so_far


def reconstruct_path(came_from: Dict, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    """根据A*算法的结果重建路径"""
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


# ==================== 游戏初始化函数 ====================
def generate_game_entities(grid_size: int, obstacle_count: int, item_count: int,
                           zombie_count: int) -> Tuple[Dict, Set, Tuple, List]:
    """
    生成游戏实体（障碍物、道具、玩家和僵尸位置）

    Returns:
         (障碍物字典, 道具集合, 玩家位置, 僵尸位置列表, 锁定物品位置)
    """
    # 所有可能的网格位置
    all_positions = [(x, y) for x in range(grid_size) for y in range(grid_size)]

    # 随机选择障碍物位置
    chosen_obstacles = random.sample(all_positions, obstacle_count)
    destructible_count = int(obstacle_count * DESTRUCTIBLE_RATIO)
    obstacles = {}

    # 创建可破坏障碍物
    for pos in chosen_obstacles[:destructible_count]:
        obstacles[pos] = Obstacle(pos, "Destructible", health=OBSTACLE_HEALTH)

    # 创建不可破坏障碍物
    for pos in chosen_obstacles[destructible_count:]:
        obstacles[pos] = Obstacle(pos, "Indestructible")

    def pick_valid_positions(min_distance: int, count: int) -> Tuple[Tuple[int, int], List[Tuple[int, int]]]:
        """选择有效位置，确保玩家和僵尸有足够距离"""
        empty_positions = [p for p in all_positions if p not in obstacles]

        while True:
            # 随机选择玩家和僵尸位置
            selected = random.sample(empty_positions, count + 1)
            player_position = selected[0]
            zombie_positions = selected[1:]

            # 检查玩家与所有僵尸的距离
            if all(abs(player_position[0] - z[0]) + abs(player_position[1] - z[1]) >= min_distance
                   for z in zombie_positions):
                return player_position, zombie_positions

    # 选择玩家和僵尸位置
    player_position, zombie_positions = pick_valid_positions(min_distance=5, count=zombie_count)

    # 生成道具位置
    forbidden_positions = set(obstacles.keys()) | {player_position} | set(zombie_positions)
    valid_positions = [p for p in all_positions if p not in forbidden_positions]
    items = set(random.sample(valid_positions, item_count))

    # 随机选择一个道具作为锁定道具
    # locked_item = random.choice(list(items))

    return obstacles, items, player_position, zombie_positions


# ----------- 生成格子地图 -----------
def build_graph(grid_size: int, obstacles: Dict[Tuple[int, int], Obstacle]) -> Graph:
    """构建游戏地图的图结构"""
    graph = Graph()

    for x in range(grid_size):
        for y in range(grid_size):
            current_pos = (x, y)

            # 跳过不可破坏障碍物
            if current_pos in obstacles and obstacles[current_pos].type == "Indestructible":
                continue

            # 检查四个方向
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor_pos = (x + dx, y + dy)

                # 确保邻居在网格范围内
                if not (0 <= neighbor_pos[0] < grid_size and 0 <= neighbor_pos[1] < grid_size):
                    continue

                # 跳过不可破坏障碍物
                if neighbor_pos in obstacles and obstacles[neighbor_pos].type == "Indestructible":
                    continue

                # 设置移动代价
                weight = 1

                # 如果是可破坏障碍物，增加移动代价
                if neighbor_pos in obstacles and obstacles[neighbor_pos].type == "Destructible":
                    weight = 10

                # 添加边
                graph.add_edge(current_pos, neighbor_pos, weight)

    return graph


# ==================== 新增游戏状态类 ====================
class GameState:
    """管理游戏状态和进度"""

    def __init__(self, obstacles: Dict, items: Set):
        self.obstacles = obstacles
        self.items = items
        # self.locked_item = locked_item
        # self.unlocked = False  # 锁定物品是否已解锁
        self.destructible_count = self.count_destructible_obstacles()
        # self.destroy_goal = destroy_goal  # 需破坏的总数（可破坏障碍总数）

    def count_destructible_obstacles(self) -> int:
        """计算可破坏障碍物的数量"""
        return sum(1 for obs in self.obstacles.values() if obs.type == "Destructible")

    # def check_unlock_condition(self) -> bool:
    #     """检查是否满足解锁条件"""
    #     # 条件1: 所有其他物品已被收集
    #     # 条件2: 所有可破坏障碍物已被破坏
    #     return len(self.items) == 1 and self.destructible_count == 0

    def collect_item(self, pos: Tuple[int, int]) -> bool:
        """收集物品，如果是锁定物品且未解锁则无法收集"""
        if pos not in self.items:
            return False

        # 如果是锁定物品且未解锁，不能收集
        # if pos == self.locked_item and not self.unlocked:
        #     return False

        self.items.remove(pos)
        return True

    def destroy_obstacle(self, pos: Tuple[int, int]):
        """破坏障碍物并更新计数"""
        if pos in self.obstacles:
            # 如果是可破坏障碍物，更新计数
            if self.obstacles[pos].type == "Destructible":
                self.destructible_count -= 1
            del self.obstacles[pos]

        # # 每次破坏后检查是否满足解锁条件
        # self.unlocked = self.check_unlock_condition()


# ==================== 游戏渲染函数 ====================


def render_game(screen: pygame.Surface, game_state, player: Player, zombies: List[Zombie]) -> None:
    """渲染游戏画面"""
    # 清空屏幕
    screen.fill((20, 20, 20))

    # 绘制网格
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (50, 50, 50), rect, 1)

    # 绘制道具
    for item_pos in game_state.items:
        # color = LOCKED_ITEM_COLOR if item_pos == game_state.locked_item and not game_state.unlocked else (255, 255, 0)
        center = (item_pos[0] * CELL_SIZE + CELL_SIZE // 2, item_pos[1] * CELL_SIZE + CELL_SIZE // 2)
        # pygame.draw.circle(screen, color, center, CELL_SIZE // 3)

        # 如果是锁定的道具，画一个锁的图标
        # if item_pos == game_state.locked_item and not game_state.unlocked:
        #     lock_rect = pygame.Rect(
        #         item_pos[0] * CELL_SIZE + CELL_SIZE // 4,
        #         item_pos[1] * CELL_SIZE + CELL_SIZE // 4,
        #         CELL_SIZE // 2,
        #         CELL_SIZE // 2
        #     )
        #     pygame.draw.rect(screen, (30, 30, 30), lock_rect, 2)

    # 绘制玩家
    player_rect = pygame.Rect(
        player.pos[0] * CELL_SIZE,
        player.pos[1] * CELL_SIZE,
        CELL_SIZE,
        CELL_SIZE
    )
    pygame.draw.rect(screen, (0, 255, 0), player_rect)

    # 绘制所有僵尸
    for zombie in zombies:
        zombie_rect = pygame.Rect(
            zombie.pos[0] * CELL_SIZE,
            zombie.pos[1] * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(screen, (255, 60, 60), zombie_rect)

    # 绘制障碍物
    for obstacle in game_state.obstacles.values():
        color = (200, 80, 80) if obstacle.type == "Destructible" else (120, 120, 120)
        obstacle_rect = pygame.Rect(
            obstacle.pos[0] * CELL_SIZE,
            obstacle.pos[1] * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(screen, color, obstacle_rect)

        # 显示可破坏障碍物的生命值
        if obstacle.type == "Destructible":
            font = pygame.font.SysFont(None, 30)
            health_text = font.render(str(obstacle.health), True, (255, 255, 255))
            screen.blit(health_text, (obstacle.pos[0] * CELL_SIZE + 6, obstacle.pos[1] * CELL_SIZE + 8))


def render_game_result(screen: pygame.Surface, result: str) -> None:
    """渲染游戏结果画面"""
    screen.fill((0, 0, 0))
    font = pygame.font.SysFont(None, 80)

    if result == "success":
        text = font.render("CONGRATULATIONS!", True, (0, 255, 0))
    elif result == "fail":
        text = font.render("GAME OVER!", True, (255, 60, 60))

    text_rect = text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.wait(1500)


# ==================== 游戏主循环 ====================
def main() -> None:
    """游戏主函数"""
    # 初始化pygame
    pygame.init()
    pygame.display.set_caption("Zombie Chase Game")
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    clock = pygame.time.Clock()

    # 生成游戏实体
    obstacles, items, player_start, zombie_starts = generate_game_entities(
        grid_size=GRID_SIZE,
        obstacle_count=OBSTACLES,
        item_count=ITEMS,
        zombie_count=ZOMBIE_NUM
    )

    # 创建游戏状态管理器
    game_state = GameState(obstacles, items)

    # 创建玩家和僵尸
    player = Player(player_start, speed=PLAYER_SPEED)
    zombies = [Zombie(pos, speed=ZOMBIE_SPEED) for pos in zombie_starts]

    # 构建地图图结构
    graph = build_graph(GRID_SIZE, obstacles)

    # 游戏状态变量
    game_running = True
    game_result = None  # "success" or "fail"

    # 主游戏循环
    while game_running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False

        # 玩家移动
        if player.move_cooldown > 0:
            player.move_cooldown -= 1

        keys = pygame.key.get_pressed()
        for key, direction in DIRECTIONS.items():
            if keys[key]:
                player.move(direction, obstacles)
                break

        # 检查玩家是否拾取道具
        if player.pos in game_state.items:
            # items.remove(player.pos)
            # 检查玩家是否拾取道具
            # if player.pos in game_state.items:
            if game_state.collect_item(player.pos):
                    # 播放收集音效
                pass
            else:
                    # 播放无法收集的音效
                pass

        # 僵尸行为
        for zombie in zombies:
            if zombie.move_cooldown > 0:
                zombie.move_cooldown -= 1
                continue

            action, target_pos = zombie.chase(player.pos, graph, obstacles)

            # 处理障碍物被破坏的情况
            if action == "destroy":
                # 更新游戏状态
                game_state.destroy_obstacle(target_pos)
                # 重建图
                graph = build_graph(GRID_SIZE, game_state.obstacles)

            # 处理僵尸移动
            if action == "move":
                zombie.pos = target_pos

            zombie.move_cooldown = zombie.speed

            # 检查僵尸是否抓到玩家
            if zombie.pos == player.pos:
                game_result = "fail"
                game_running = False

        # 检查胜利条件（收集所有道具）
        if not game_state.items and game_result is None:
            game_result = "success"
            game_running = False

        # 渲染游戏
        render_game(screen, game_state, player, zombies)
        # 显示剩余障碍物和物品计数
        font = pygame.font.SysFont(None, 24)
        obstacles_text = font.render(f"BLOCKS: {game_state.destructible_count}", True, (200, 80, 80))
        items_text = font.render(f"ITEMS: {len(game_state.items)}", True, (255, 255, 0))
        screen.blit(obstacles_text, (10, 10))
        screen.blit(items_text, (10, 40))

        # # 如果锁定物品未解锁，显示提示
        # if game_state.locked_item in game_state.items and not game_state.unlocked:
        #     hint_text = font.render("BREAK ALL THE BLOCKS TO UNLOCK THE LAST ITEM!", True, (100, 200, 255))
        #     screen.blit(hint_text, (WINDOW_SIZE // 2 - 150, 10))
        pygame.display.flip()
        clock.tick(15)

    # 显示游戏结果
    if game_result:
        render_game_result(screen, game_result)

    # 退出游戏
    pygame.quit()


if __name__ == "__main__":
    main()

# TODO
#  IMPROVE THE UI AND HINT  BUGS ABOUT LOCKED ITEM CANNOT SUCCESS/ block arrangement
#  ADDING MULTIPLE TYPE/ NUMBER OF / Balancing the speed of Zombies & Player
#  Adding more interaction with the blocks and other feature on map
#  Adding multiple chapters afterMONSTER AGAINST PLAYER  DONE
#  Possibly increase player ability completing single one
#  新怪物/AI
#  更多交互/可破坏物体
#  动画、特效、音效
#  UI按钮、菜单、地图选择等
#  Actually you know what I got I better idea about this game, Zombie and Obstacle,
#  We can make it have a much deeper connection with player, add them into the goal of the game
#  Revision: put the last item in the centre of walls surrounding, do not use the lock thing
#  , it has nothing to do directly with the game set
#  Add a potion to control zombie possess the body


# Had to remove all the locked item to change to another style which is more reasonable for Gaming
# And btw still figuring the UI