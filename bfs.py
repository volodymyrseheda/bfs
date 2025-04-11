#!/usr/bin/env python3
import sys
import os
import random
import time
from collections import deque
from enum import Enum
# Settings for Linux
import tty
import termios

class Color(Enum):
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"

class GridWorld:
    def __init__(self, width=30, height=30, obstacle_density=0.15):
        self.width = width
        self.height = height
        self.reset_world(obstacle_density)
        
    def reset_world(self, obstacle_density):
        """Resets the world to its original state"""
        self.agent_pos = [0, 0]
        self.goal_pos = [self.width-1, self.height-1]
        self.obstacles = self._generate_obstacles(obstacle_density)
        self.auto_pilot = False
        self.path = []
        self.visited = set()
        
        # Symbols to display
        self.agent_char = f"{Color.BLUE.value}▲{Color.RESET.value}"
        self.goal_char = f"{Color.GREEN.value}★{Color.RESET.value}"
        self.obstacle_char = f"{Color.RED.value}█{Color.RESET.value}"
        self.empty_char = f"{Color.CYAN.value}·{Color.RESET.value}"
        self.path_char = f"{Color.YELLOW.value}•{Color.RESET.value}"
        self.visited_char = f"{Color.MAGENTA.value}○{Color.RESET.value}"

    def _generate_obstacles(self, density):
        """Generates random interference"""
        obstacles = []
        total_cells = self.width * self.height
        num_obstacles = int(total_cells * density)
        while len(obstacles) < num_obstacles:
            x = random.randint(0, self.height-1)
            y = random.randint(0, self.width-1)
            pos = [x, y]
            if pos != self.agent_pos and pos != self.goal_pos and pos not in obstacles:
                obstacles.append(pos)
        return obstacles
    
    def _bfs_search(self):
        """Path finding using BFS"""
        queue = deque([(self.agent_pos, [])])
        visited = set([tuple(self.agent_pos)])
        directions = [(-1,0,'up'), (1,0,'down'), (0,-1,'left'), (0,1,'right')]
        while queue:
            (x, y), path = queue.popleft()
            if [x, y] == self.goal_pos:
                self.visited = visited
                return path
            for dx, dy, direction in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.height and 0 <= ny < self.width and 
                    tuple([nx, ny]) not in visited and 
                    [nx, ny] not in self.obstacles):
                    visited.add(tuple([nx, ny]))
                    queue.append(([nx, ny], path + [direction]))
        return None
    
    def start_auto_pilot(self):
        """Enabling autopilot"""
        self.auto_pilot = True
        self.path = self._bfs_search()
        
        if not self.path:
            print(f"{Color.RED.value}Path not found!{Color.RESET.value}")
            self.auto_pilot = False
            return False
        
        print(f"{Color.GREEN.value}Autopilot activated!{Color.RESET.value}")
        return True
    
    def move_agent(self, direction=None):
        """Agent movement (for manual and auto mode)"""
        if direction is None and self.auto_pilot and self.path:
            direction = self.path.pop(0)
        x, y = self.agent_pos
        new_pos = [x, y]
        if direction == 'up':
            new_pos[0] = max(0, x - 1)
        elif direction == 'down':
            new_pos[0] = min(self.height - 1, x + 1)
        elif direction == 'left':
            new_pos[1] = max(0, y - 1)
        elif direction == 'right':
            new_pos[1] = min(self.width - 1, y + 1)
        else:
            return False, -1
        if new_pos in self.obstacles:
            return False, -1
        self.agent_pos = new_pos
        reached_goal = (self.agent_pos == self.goal_pos)
        reward = 10 if reached_goal else -0.1
        return reached_goal, reward
    
    def render(self):
        """Game Visualization"""
        os.system('clear')
        mode = "AUTOPILOT" if self.auto_pilot else "MANUAL"
        print(f"{Color.YELLOW.value}=== GAME WORLD with BFS algorithm [{mode}] ===")
        print(f"Management: Arrows/WASD | Q: Autopilot | R: Restart | ESC: Exit {Color.RESET.value}")
        for x in range(self.height):
            for y in range(self.width):
                pos = [x, y]
                if pos == self.agent_pos:
                    print(self.agent_char, end=" ")
                elif pos == self.goal_pos:
                    print(self.goal_char, end=" ")
                elif pos in self.obstacles:
                    print(self.obstacle_char, end=" ")
                elif self.auto_pilot and tuple(pos) in self.visited:
                    print(self.visited_char, end=" ")
                else:
                    print(self.empty_char, end=" ")
            print()
        print(f"\n{Color.CYAN.value}Agent: {self.agent_pos} | Target: {self.goal_pos} | Obstacles: {len(self.obstacles)}")
        if self.auto_pilot and self.path:
            print(f"{Color.YELLOW.value}Steps left: {len(self.path)}{Color.RESET.value}")

def get_key():
    """Getting the key pressed"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        
        if ch == '\x1b':
            ch = sys.stdin.read(1)
            if ch == '[':
                ch = sys.stdin.read(1)
                return {'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left'}.get(ch)
            elif ch == '\x1b':
                return 'esc'
        return {'q': 'q', 'w': 'up', 's': 'down', 
                'a': 'left', 'd': 'right', 'r': 'r'}.get(ch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    env = GridWorld() 
    try:
        while True:
            env.render()
            if env.auto_pilot:
                # Автоматичний рух
                success, reward = env.move_agent()
                print(f"{Color.YELLOW.value}Reward: {reward}{Color.RESET.value}")
                time.sleep(0.3)
                if success:
                    print(f"\n{Color.GREEN.value}=== GOAL ACHIEVED ==={Color.RESET.value}")
                    time.sleep(2)
                    env.reset_world(0.15)
                elif not env.path:
                    print(f"{Color.RED.value}The path is over!{Color.RESET.value}")
                    env.auto_pilot = False
                    time.sleep(1)
                continue
            key = get_key()
            if key == 'esc':
                break
            elif key == 'r':
                env.reset_world(0.15)
            elif key == 'q':
                if env.auto_pilot:
                    env.auto_pilot = False
                    print(f"{Color.YELLOW.value}Autopilot off!{Color.RESET.value}")
                else:
                    if env.start_auto_pilot():
                        continue
                time.sleep(1)
            elif key in ('up', 'down', 'left', 'right'):
                success, reward = env.move_agent(key)
                print(f"{Color.YELLOW.value}Reward: {reward}{Color.RESET.value}")
                if success:
                    print(f"\n{Color.GREEN.value}=== GOAL ACHIEVED ==={Color.RESET.value}")
                    time.sleep(2)
                    env.reset_world(0.15)
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW.value}The game is over.{Color.RESET.value}")
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, termios.tcgetattr(sys.stdin.fileno()))

if __name__ == "__main__":
    main()