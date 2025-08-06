# Zombie Chase: Lockdown Edition
================DEVELOPING IN PROGRESS====================
## Overview

Zombie Chase: Lockdown Edition is a thrilling strategy-survival game where you must outsmart and outmaneuver relentless zombies in a dynamically changing environment. Collect items to survive, but beware - the final item is locked behind all obstacles! Use the zombies' destructive nature to your advantage as you strategically guide them to clear your path.

## Key Features

Strategic Gameplay: Balance item collection with obstacle destruction

Locked Final Item: The last reward requires clearing all obstacles

Smart Zombies: AI-controlled zombies that adapt their behavior

Destructible Environments: Two types of obstacles - breakable and unbreakable

Risk-Reward Mechanics: Every move counts in this high-stakes chase

Dynamic Map Generation: New challenges every playthrough

## How to Play
## Objective
Collect all items on the map to win. But there's a catch - the final item is locked until you destroy all breakable obstacles!

Controls
WASD: Move your character (green square)

Arrow Keys: Alternative movement controls

Mechanics
🟢 Player: Collect yellow items while avoiding zombies

🧟 Zombies: Will chase you relentlessly and destroy breakable obstacles

🟫 Breakable Obstacles: Brown blocks that zombies can destroy

🪨 Unbreakable Obstacles: Gray blocks that block all paths

🔒 Locked Item: Blue item that requires all obstacles to be destroyed

Win Conditions
✅ Win: Collect all items after destroying all breakable obstacles

❌ Lose: Get caught by a zombie before collecting all items

Installation
Requirements
Python 3.8+

Pygame 2.0+

Quick Start
bash
## Clone the repository
git clone https://github.com/yourusername/zombie-chase.git

## Navigate to project directory
cd zombie-chase

## Install dependencies
pip install pygame

## Run the game
python ZGame.py
Game Strategies
Bait and Switch: Lure zombies to obstacles you need destroyed

Path Manipulation: Use obstacles to create safe zones

Efficiency First: Plan routes to collect items while zombies clear paths

Last Stand: When going for the final item, make sure escape routes are clear!

Customization
Easily modify game parameters in the code:

python
## Game settings
GRID_SIZE = 18               # Size of game grid
CELL_SIZE = 40               # Pixel size of each cell
OBSTACLES_COUNT = 25         # Number of obstacles
OBSTACLE_HEALTH = 20         # Health of destructible obstacles
DESTRUCTIBLE_RATIO = 0.4     # Percentage of breakable obstacles
PLAYER_SPEED = 2             # Player movement speed (lower = faster)
ZOMBIE_SPEED = 5             # Zombie movement speed (lower = faster)
ZOMBIE_ATTACK = 10           # Zombie attack damage to obstacles
ZOMBIE_COUNT = 2             # Number of zombies
ITEMS_COUNT = 10             # Number of items to collect
Future Roadmap
Multiple zombie types with special abilities

Player power-ups and special moves

Day/night cycle affecting gameplay

Progressive difficulty levels

Multiplayer cooperative mode

================DEVELOPING IN PROGRESS====================

License
This project is licensed under the MIT License - see the LICENSE.md file for details.

Survive. Strategies. Escape. Will you unlock your freedom or become prey to zombies? The choice is yours!

entities.py：Player, Zombie, Obstacle, MainBlock, Item 

level.py：LEVELS，get_level_config, generate_game_entities

state.py：GameState

utils.py：sign, heuristic, a_star_search, reconstruct_path 

menu.py：show_start_menu

game_render.py：render_game

result_screen.py：render_game_result

main.py：流程控制（菜单->关卡->结算->下关）