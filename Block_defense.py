import pygame
import math
import sys
from pathlib import Path

pygame.init()
font = pygame.font.SysFont(None, 30)

game_dir = Path(__file__).parent

block_group = []

# Screen setup
surface = pygame.display.set_mode((900, 700))
clock = pygame.time.Clock()
#Name
pygame.display.set_caption("Block_defense")

#Hover over the blocks to see what they do
towers_info = {
    "Rect": {
        "rect": pygame.Rect(750, 100, 50, 50),
        "description": "Basic tower. Shoots bullets at enemies."
    },
    "fusion1": {
        "rect": pygame.Rect(750, 160, 50, 50),
        "description": "Fast shooting tower."
    },
    "fusion2": {
        "rect": pygame.Rect(750, 220, 50, 50),
        "description": "Powerful bullets but slower and also makes money."
    }
}
def draw_tooltip(screen, text, pos, font):
    # Render the text surface
    tooltip_surface = font.render(text, True, (255, 255, 255))
    
    # Get size and create background rectangle slightly bigger than text
    padding = 5
    bg_rect = tooltip_surface.get_rect(topleft=(pos[0] + 10, pos[1] + 10))
    bg_rect.inflate_ip(padding * 2, padding * 2)
    
    # Make sure tooltip doesn't go off the screen to the right or bottom
    if bg_rect.right > screen.get_width():
        bg_rect.right = screen.get_width() - 5
    if bg_rect.bottom > screen.get_height():
        bg_rect.bottom = screen.get_height() - 5
    
    # Draw a dark background rect with slight transparency
    s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))  # Black with alpha transparency
    screen.blit(s, bg_rect.topleft)
    
    # Draw the text on top of the background
    screen.blit(tooltip_surface, (bg_rect.left + padding, bg_rect.top + padding))



# === Block Classes ===
class Block:
    def __init__(self, path, color=(0,255,0), health=100, speed=1):
        self.path = path
        self.current_point = 0
        self.x, self.y = path[0]
        self.color = color
        self.max_health, self.health = health, health
        self.speed = speed
        self.alive = True
        # Poison attributes
        self.poisoned = False
        self.poison_timer = 0
        self.poison_duration = 0
        self.poison_damage = 0
        self.poison_tick_rate = 0
        self.last_poison_tick = 0

    def move(self):
        # Move along the waypoint path
        if self.current_point < len(self.path) - 1:
            tx, ty = self.path[self.current_point + 1]
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed:
                self.x, self.y = tx, ty
                self.current_point += 1
            else:
                self.x += self.speed * dx / dist
                self.y += self.speed * dy / dist
        else:
            self.alive = False  # reached the end

    def take_damage(self, dmg):
        """Reduce health and mark death if zero."""
        self.health -= dmg
        if self.health <= 0:
            self.alive = False

    def apply_poison(self, duration, dmg_tick, tick_rate, current_time):
        """Init poison effect with timers."""
        self.poisoned = True
        self.poison_duration = duration
        self.poison_damage = dmg_tick
        self.poison_tick_rate = tick_rate
        self.last_poison_tick = current_time
        self.poison_timer = 0

    def update_poison(self, current_time):
        """Apply poison tick damage over time."""
        if not self.poisoned:
            return
        if current_time - self.last_poison_tick >= self.poison_tick_rate:
            self.take_damage(self.poison_damage)
            self.last_poison_tick = current_time
        self.poison_timer += current_time - self.last_poison_tick
        if self.poison_timer >= self.poison_duration:
            self.poisoned = False

    def render(self, surface):
        """Draw enemy and its health bar."""
        size = 40
        rect = pygame.Rect(self.x - size/2, self.y - size/2, size, size)
        pygame.draw.rect(surface, self.color, rect)

        # Health bar
        bar_w, bar_h = size, 5
        ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(surface, (255,0,0), (rect.left, rect.top - bar_h - 2, bar_w, bar_h))
        pygame.draw.rect(surface, (0,255,0), (rect.left, rect.top - bar_h - 2, bar_w * ratio, bar_h))


#Passing all of the block stuff to the other three
class Block2(Block):           # Strong and medium-fast
    def __init__(self, path):
        super().__init__(path, color=(255,100,0), health=120, speed=0.8)

class Block_small(Block):     # Fast but fragile
    def __init__(self, path):
        super().__init__(path, color=(100,200,255), health=60, speed=1.5)

class Block_large(Block):     # Slow but durable
    def __init__(self, path):
        super().__init__(path, color=(120,120,120), health=200, speed=0.5)





# Global gold variable (make sure you define it in your main code)
Gold = 0

# === Bullet Class ===
class Bullet:
    def __init__(self, x, y, speed, color, size, angle, damage, poison=False):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size
        self.radius = size // 2
        self.angle = angle
        self.damage = damage
        self.poison = poison
        self.hit = False

    def move(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

    def render(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def get_hitbox(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

# === Base Tower Class ===
class Rect:
    def __init__(self, x, y, color, size, damage):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.damage = damage
        self.alive = True
        self.bullets = []
        self.fire_interval = 2000  # milliseconds between shots
        self.last_fire_time = pygame.time.get_ticks()

    def render(self, screen, target=None):
        # Draw tower, optionally rotated towards target
        if target and self.alive:
            dx = target.x - self.x
            dy = target.y - self.y
            angle = math.atan2(dy, dx)
            half = self.size // 2
            rect_points = [(-half, -half), (half, -half), (half, half), (-half, half)]
            rotated_points = []
            for px, py in rect_points:
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                rotated_points.append((self.x + rx, self.y + ry))
            pygame.draw.polygon(screen, self.color, rotated_points)
        else:
            rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
            pygame.draw.rect(screen, self.color, rect)

    def fire_bullet(self, target):
        if target is None:
            return  # No target to fire at
        dx = target.x - self.x
        dy = target.y - self.y
        angle = math.atan2(dy, dx)
        speed = 3
        bullet_size = 10
        bullet_color = (0, 0, 0)
        self.bullets.append(Bullet(self.x, self.y, speed, bullet_color, bullet_size, angle, self.damage))

    def update(self, current_time, blocks_list, screen):
        global Gold
        # Fire bullet if fire interval elapsed and there is a live target
        if current_time - self.last_fire_time > self.fire_interval:
            target_block = next((block for block in blocks_list if block.alive), None)
            if target_block:
                self.fire_bullet(target_block)
                self.last_fire_time = current_time

        # Update bullets: move, render, and check collisions
        for bullet in self.bullets[:]:
            bullet.move()
            bullet.render(screen)

            hit = False
            for block in blocks_list:
                if block.alive and bullet.get_hitbox().colliderect(block.get_hitbox()):
                    self.bullets.remove(bullet)
                    block.health -= self.damage
                    if block.health <= 0:
                        block.alive = False
                        Gold += 10  # Adjust reward as needed
                    hit = True
                    break
            if hit:
                continue

# === Money Maker Tower ===
class MoneyMaker:
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.money_interval = 3000  # milliseconds
        self.last_money_time = pygame.time.get_ticks()

    def render(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

    def update(self, current_time):
        global Gold
        if current_time - self.last_money_time > self.money_interval:
            Gold += 5
            self.last_money_time = current_time

# === Booster Tower (Supports nearby towers) ===
class BoosterTower:
    def __init__(self, x, y, color, size):
        self.name = "booster"
        self.x = x
        self.y = y
        self.size = size
        self.range = 100
        self.boost_applied = False
        self.damage = 0  # Does not shoot
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        pygame.draw.circle(surface, (0, 255, 255), (self.x, self.y), self.range, 1)

    def apply_boost(self, towers):
        if self.boost_applied:
            return
        for tower in towers:
            if tower is not self and hasattr(tower, 'damage') and tower.damage > 0:
                dist = math.hypot(self.x - tower.x, self.y - tower.y)
                if dist <= self.range:
                    tower.damage = int(tower.damage * 1.2)
        self.boost_applied = True

    def render(self, surface):
        self.draw(surface)

# === Fusion Tower Classes ===
class FusionTowerBase:
    def __init__(self, x, y, color, size, damage=3, fire_interval=2000):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.damage = damage
        self.bullets = []
        self.fire_interval = fire_interval
        self.last_fire_time = pygame.time.get_ticks()

    def render(self, screen, target=None):
        if target:
            dx = target.x - self.x
            dy = target.y - self.y
            angle = math.atan2(dy, dx)
            half = self.size // 2
            rect_points = [(-half, -half), (half, -half), (half, half), (-half, half)]
            rotated_points = []
            for px, py in rect_points:
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                rotated_points.append((self.x + rx, self.y + ry))
            pygame.draw.polygon(screen, self.color, rotated_points)
        else:
            pygame.draw.rect(screen, self.color,
                             (self.x - self.size // 2, self.y - self.size // 2, self.size, self.size))

    def fire_bullet(self, target):
        if target is None:
            return
        dx = target.x - self.x
        dy = target.y - self.y
        angle = math.atan2(dy, dx)
        speed = 3
        bullet_size = 10
        bullet_color = (0, 0, 0)
        self.bullets.append(Bullet(self.x, self.y, speed, bullet_color, bullet_size, angle, self.damage))

    def update(self, current_time, blocks_list, screen):
        global Gold
        # Fire bullet if possible
        if current_time - self.last_fire_time > self.fire_interval:
            target_block = next((block for block in blocks_list if block.alive), None)
            if target_block:
                self.fire_bullet(target_block)
                self.last_fire_time = current_time

        # Update bullets (move, render, collision)
        for bullet in self.bullets[:]:
            bullet.move()
            bullet.render(screen)

            hit = False
            for block in blocks_list:
                if block.alive and bullet.get_hitbox().colliderect(block.get_hitbox()):
                    self.bullets.remove(bullet)
                    block.health -= self.damage
                    if block.health <= 0:
                        block.alive = False
                        Gold += 10  # Adjust gold reward accordingly
                    hit = True
                    break
            if hit:
                continue

class Fusion1(FusionTowerBase):
    pass  # Inherits everything from FusionTowerBase

class Fusion2(FusionTowerBase):
    def __init__(self, x, y, color, size):
        super().__init__(x, y, color, size)
        self.money_interval = 5000
        self.last_money_time = pygame.time.get_ticks()
        self.money_amount = 3

    def update_money(self, current_time):
        global Gold
        if current_time - self.last_money_time > self.money_interval:
            Gold += self.money_amount
            self.last_money_time = current_time

    def update(self, current_time, blocks_list, screen):
        super().update(current_time, blocks_list, screen)
        self.update_money(current_time)


# === Fused Tower (combines features of Fusion1 and Fusion2) ===
class Fused(FusionTowerBase):
    def __init__(self, x, y, color, size):
        super().__init__(x, y, color, size)
        self.money_interval = 5000
        self.last_money_time = pygame.time.get_ticks()

    def update(self, current_time, blocks_list, screen):
        super().update(current_time, blocks_list, screen)
        self.update_money(current_time)

    def update_money(self, current_time):
        global Gold
        if current_time - self.last_money_time > self.money_interval:
            Gold += 7
            self.last_money_time = current_time





# Reset the game state to initial values
def reset_game():
    global Gold, placed_towers, placed_money_towers, placed_fusion1, placed_fusion2, made_fusion, placed_BoosterTower
    global blocks, blocks2, blocks3, blocks4
    global player_base_health, spawn_time_1, spawn_time_2, spawn_time_3, spawn_time_4
    global dragging_tower, dragging_money, dragging_fusion1, dragging_fusion2, dragging_BoosterTower, dragging_Posion

    Gold = 10
    player_base_health = 10
    current_time = pygame.time.get_ticks()
    spawn_time_1 = spawn_time_2 = spawn_time_3 = spawn_time_4 = current_time

    placed_towers = []
    placed_money_towers = []
    placed_fusion1 = []
    placed_fusion2 = []
    made_fusion = []
    placed_BoosterTower = []

    blocks = []
    blocks2 = []
    blocks3 = []
    blocks4 = []

    dragging_tower = False
    dragging_money = False
    dragging_fusion1 = False
    dragging_fusion2 = False
    dragging_BoosterTower = False
    dragging_Posion = False


# Menu UI class for showing tower/money icons
class Menu:
    def __init__(self, x, y, color, width, height):
        self.x = x
        self.y = y
        self.color = color
        self.width = width
        self.height = height

    def render(self, screen):
        # Draw menu panel background
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

        # Draw tower icons as colored squares (you can replace with images)
        pygame.draw.rect(screen, (255, 0, 0), (self.x + 50, self.y + 50, 40, 40))      # Tower icon (red)
        pygame.draw.rect(screen, (255, 215, 0), (self.x + 100, self.y + 50, 40, 40))    # Money tower icon (gold)
        pygame.draw.rect(screen, (255, 100, 50), (self.x + 50, self.y + 100, 40, 40))   # Fusion1 icon (orange)
        pygame.draw.rect(screen, (50, 100, 50), (self.x + 100, self.y + 100, 40, 40))   # Fusion2 icon (dark green)
        pygame.draw.rect(screen, (0, 0, 255), (self.x + 50, self.y + 150, 40, 40))      # Booster tower icon (blue)


# === Initial Game Setup ===

# Define the enemy path as list of waypoints
path = [(0, 50), (450, 50), (450, 450), (0, 450)]

# Create a single example tower (could be your starting tower)
rect = Rect(200, 200, (255, 0, 0), 40, 1)

# Create menu panel instance
menu_panel = Menu(700, 0, (50, 50, 50), 200, 700)

# Enemy groups by type/size/color
blocks = []      # Normal black blocks
blocks2 = []     # Orange blocks
blocks3 = []     # Small blue blocks
blocks4 = []     # Large red blocks

# Initialize spawn timers to current time
current_time = pygame.time.get_ticks()
spawn_time_1 = spawn_time_2 = spawn_time_3 = spawn_time_4 = current_time

# Player status and resources
player_base_health = 10
Gold = 10

# Dragging flags for placing towers
dragging_tower = False
dragging_money = False
dragging_fusion1 = False
dragging_fusion2 = False
dragging_BoosterTower = False

# Lists of placed towers of different types
placed_towers = []
placed_money_towers = []
placed_fusion1 = []
placed_fusion2 = []
made_fusion = []
placed_BoosterTower = []

# Tower size for placement and hitbox calculations
tower_size = 40

# Define rectangles for menu icon hitboxes (for input detection)
tower_icon_rect = pygame.Rect(menu_panel.x + 50, menu_panel.y + 50, 40, 40)
money_icon_rect = pygame.Rect(menu_panel.x + 100, menu_panel.y + 50, 40, 40)
fusion1_icon_rect = pygame.Rect(menu_panel.x + 50, menu_panel.y + 100, 40, 40)
fusion2_icon_rect = pygame.Rect(menu_panel.x + 100, menu_panel.y + 100, 40, 40)
BoosterTower_icon_rect = pygame.Rect(menu_panel.x + 50, menu_panel.y + 150, 40, 40)


# === Game Loop ===
while True:
    reset_game()  # Reset all game variables
    running = True
    
    while running:
        current_time = pygame.time.get_ticks()
        
        # === HANDLE EVENTS ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if tower_icon_rect.collidepoint(event.pos):
                    dragging_tower = True
                elif money_icon_rect.collidepoint(event.pos):
                    dragging_money = True
                elif fusion1_icon_rect.collidepoint(event.pos):
                    dragging_fusion1 = True
                elif fusion2_icon_rect.collidepoint(event.pos):
                    dragging_fusion2 = True
                elif BoosterTower_icon_rect.collidepoint(event.pos):
                    dragging_BoosterTower = True
                else:
                    # Damage block2 on click
                    for block2 in blocks2[:]:
                        if block2.get_hitbox().collidepoint(event.pos):
                            block2.health -= 1
                            if block2.health <= 0:
                                block2.alive = False
                                Gold += 4
                            break

            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = event.pos
                tower_rect = pygame.Rect(x - 20, y - 20, 40, 40)
                valid_placement = True

                # Avoid placing on path area (with padding)
                path_width = 30
                for i in range(len(path) - 1):
                    start, end = path[i], path[i + 1]
                    line_rect = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                                            abs(start[0] - end[0]) or 1, abs(start[1] - end[1]) or 1)
                    line_rect.inflate_ip(path_width, path_width)
                    if tower_rect.colliderect(line_rect):
                        valid_placement = False
                        break

                # Avoid overlapping existing towers
                all_towers = (placed_towers + placed_money_towers + placed_fusion1 +
                              placed_fusion2 + made_fusion + placed_BoosterTower)
                for turret in all_towers:
                    existing_rect = pygame.Rect(turret.x - turret.size // 2,
                                                turret.y - turret.size // 2,
                                                turret.size, turret.size)
                    if tower_rect.colliderect(existing_rect):
                        valid_placement = False
                        break

                # Place towers if valid and enough Gold, and within play area (left of menu)
                if x >= menu_panel.x:
                    valid_placement = False

                if dragging_tower and Gold >= 3 and valid_placement:
                    placed_towers.append(Rect(x, y, (255, 0, 0), 40, 1))
                    Gold -= 3

                elif dragging_money and Gold >= 7 and valid_placement:
                    placed_money_towers.append(money_maker(x, y, (255, 215, 0), 40))
                    Gold -= 7

                elif dragging_BoosterTower and Gold >= 15 and valid_placement:
                    placed_BoosterTower.append(BoosterTower(x, y, (0, 0, 255), 40))
                    Gold -= 15

                elif dragging_fusion1 and Gold >= 12:
                    fusion_rect = pygame.Rect(x - 20, y - 20, 40, 40)
                    fusion2_found = None
                    for turret in placed_fusion2:
                        existing_rect = pygame.Rect(turret.x - turret.size // 2,
                                                    turret.y - turret.size // 2,
                                                    turret.size, turret.size)
                        if fusion_rect.colliderect(existing_rect):
                            fusion2_found = turret
                            break
                    if fusion2_found:
                        placed_fusion2.remove(fusion2_found)
                        made_fusion.append(fused(x, y, (128, 0, 128), 40))
                        Gold -= 12
                    elif valid_placement:
                        placed_fusion1.append(fusion1(x, y, (255, 100, 50), 40))
                        Gold -= 12

                elif dragging_fusion2 and Gold >= 20:
                    fusion_rect = pygame.Rect(x - 20, y - 20, 40, 40)
                    fusion1_found = None
                    for turret in placed_fusion1:
                        existing_rect = pygame.Rect(turret.x - turret.size // 2,
                                                    turret.y - turret.size // 2,
                                                    turret.size, turret.size)
                        if fusion_rect.colliderect(existing_rect):
                            fusion1_found = turret
                            break
                    if fusion1_found:
                        placed_fusion1.remove(fusion1_found)
                        made_fusion.append(fused(x, y, (128, 0, 128), 40))
                        Gold -= 20
                    elif valid_placement:
                        placed_fusion2.append(fusion2(x, y, (50, 100, 50), 40))
                        Gold -= 20

                # Reset dragging flags
                dragging_tower = dragging_money = dragging_fusion1 = dragging_fusion2 = dragging_BoosterTower = False

        # === HANDLE KEYS ===
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_r] and player_base_health <= 0:
            # Restart game if dead and player presses R
            running = False

        # === UPDATE SPAWN TIMERS & SPAWN ENEMIES ===
        if current_time - spawn_time_1 > 5000:
            block = Block(path)
            block.color = block_color
            block.health = 3
            block.speed = 1
            block.size = block_size
            blocks3.append(block)
            spawn_time_1 = current_time

        if current_time - spawn_time_2 > 10000:
            block = Block_large(path)
            block.color = block4_color
            block.health = 5
            block.speed = 0.5
            block.size = block4_size
            blocks3.append(block)
            spawn_time_2 = current_time

        if current_time - spawn_time_3 > 3000:
            block = Block_small(path)
            block.color = block3_color
            block.health = 1
            block.speed = 1.5
            block.size = block3_size
            blocks3.append(block)
            spawn_time_3 = current_time

        if current_time - spawn_time_4 > 20000:
            block = Block2(path)
            block.color = block_color
            block.health = 3
            block.speed = 1
            block.size = block_size
            blocks2.append(block)
            spawn_time_4 = current_time

        # === ENEMY MOVEMENT & RENDERING ===
        for group, health_loss in zip([blocks, blocks2, blocks3, blocks4], [2, 3, 1, 5]):
            for block in group[:]:
                reached = block.move()
                block.render(surface)
                if not block.alive:
                    group.remove(block)
                    if reached:
                        player_base_health -= health_loss

        # === TOWER FIRING & BULLET UPDATES ===
        # (Assuming firing and bullet render methods take surface as argument)
        for turrets, multiplier, block_d in [
            (placed_towers, 1, 1),
            (placed_fusion1, 1, 2),
            (placed_fusion2, 3, 1),
            (made_fusion, 5, 3),
            (placed_BoosterTower, 0, 0)
        ]:
            for turret in turrets:
                if isinstance(turret, BoosterTower):
                    continue

                for target, _, _ in [
                    (next((b for b in blocks if b.alive), None), blocks, 2),
                    (next((b for b in blocks3 if b.alive), None), blocks3, 1),
                    (next((b for b in blocks4 if b.alive), None), blocks4, 4)
                ]:
                    if target and current_time - turret.last_fire_time > turret.fire_interval:
                        if getattr(turret, "is_poison", False):
                            turret.fire_poison_bullet(target)
                        else:
                            turret.fire_bullet(target)
                        turret.last_fire_time = current_time
                        break

                bullets_to_remove = []
                Gold_to_add = 0

                for bullet in turret.bullets[:]:
                    bullet.move()
                    bullet.render(surface)
                    hit_something = False

                    for target_tuple in [
                        (next((b for b in blocks if b.alive), None), blocks, 2),
                        (next((b for b in blocks3 if b.alive), None), blocks3, 1),
                        (next((b for b in blocks4 if b.alive), None), blocks4, 4)
                    ]:
                        target = target_tuple[0]
                        if target and bullet.get_hitbox().colliderect(target.get_hitbox()):
                            target.take_damage(bullet.damage)
                            if getattr(bullet, "poison", False):
                                target.apply_poison()
                            hit_something = True
                            break

                    if not hit_something:
                        for _, block_group, gold_reward in [
                            (None, blocks, 2),
                            (None, blocks3, 1),
                            (None, blocks4, 4)
                        ]:
                            for block in block_group:
                                if block.alive and bullet.get_hitbox().colliderect(block.get_hitbox()):
                                    bullet.hit_target()
                                    block.health -= block_d
                                    if getattr(bullet, "poison", False):
                                        block.apply_poison()
                                    if block.health <= 0:
                                        block.alive = False
                                        Gold_to_add += gold_reward * multiplier
                                    hit_something = True
                                    break
                            if hit_something:
                                break

                    if hit_something:
                        bullets_to_remove.append(bullet)

                for bullet in bullets_to_remove:
                    if bullet in turret.bullets:
                        turret.bullets.remove(bullet)

                Gold += Gold_to_add

        # === MONEY GENERATION ===
        for m in placed_money_towers:
            m.render(surface)
            m.update(current_time)
        for n in made_fusion:
            n.render(surface)
            n.update_money(current_time)

        # === BOOSTER TOWER EFFECTS ===
        for booster in placed_BoosterTower:
            booster.draw(surface)
            booster.apply_boost(placed_towers + placed_fusion1 + placed_fusion2 + made_fusion)

        # === RENDER TOWERS ===
        for tower in placed_towers:
            tower.render(surface)
        for tower in placed_fusion1:
            tower.render(surface)
        for tower in placed_fusion2:
            tower.render(surface)
        for tower in made_fusion:
            tower.render(surface)

        # === DRAW MENU AND UI ===
        surface.fill((255, 255, 255))
        pygame.draw.lines(surface, (200, 200, 200), False, path, 2)
        menu_panel.render(surface)

        # Draw Gold
        coin_x, coin_y, coin_radius = menu_panel.x + 25, menu_panel.y + 20, 12
        pygame.draw.circle(surface, (218, 165, 32), (coin_x, coin_y), coin_radius)
        pygame.draw.circle(surface, (184, 134, 11), (coin_x, coin_y), coin_radius, 2)
        pygame.draw.arc(surface, (255, 255, 255), (coin_x - 8, coin_y - 8, 16, 16), math.pi * 0.25, math.pi * 0.75, 2)
        gold_text = font.render(f"{Gold}", True, (255, 255, 255))
        gold_rect = gold_text.get_rect(midleft=(coin_x + 20, coin_y))
        surface.blit(gold_text, gold_rect)

        # Draw dragging preview
        if dragging_tower or dragging_money or dragging_fusion1 or dragging_fusion2 or dragging_BoosterTower:
            mx, my = pygame.mouse.get_pos()
            color = (255, 0, 0) if dragging_tower else \
                    (255, 215, 0) if dragging_money else \
                    (255, 100, 50) if dragging_fusion1 else \
                    (50, 100, 50) if dragging_fusion2 else \
                    (0, 0, 255) if dragging_BoosterTower else \
                    (0, 0, 255)
            pygame.draw.rect(surface, color, (mx - 20, my - 20, 40, 40))

        # === BASE HEALTH BAR ===
        pygame.draw.rect(surface, (150, 150, 150), (10, 10, 200, 20))
        pygame.draw.rect(surface, (0, 200, 0), (10, 10, 200 * (player_base_health / 10), 20))

        # === GAME OVER SCREEN ===
        if player_base_health <= 0:
            game_over_font = pygame.font.SysFont(None, 50)
            info_font = pygame.font.SysFont(None, 36)
            surface.blit(game_over_font.render("Game Over", True, (255, 0, 0)), (350, 300))
            surface.blit(info_font.render("Press R to Play Again or ESC to Quit", True, (0, 0, 0)), (250, 350))
            pygame.display.flip()

            waiting_for_input = True
            while waiting_for_input:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            waiting_for_input = False
                            running = False  # restart outer loop
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
            break  # exit current loop to restart or quit

        # === TOOLTIP ON ICON HOVER ===
        mouse_pos = pygame.mouse.get_pos()
        if tower_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(surface, "Basic Tower: Shoots at enemies. Cost: 3", mouse_pos, font)
        elif money_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(surface, "Money Tower: Generates gold over time. Cost: 7", mouse_pos, font)
        elif fusion1_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(surface, "Fusion1 Tower: Shoots powerful bullets. Combine with Fusion2. Cost: 12", mouse_pos, font)
        elif fusion2_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(surface, "Fusion2 Tower: Slower shooter + money generation. Combine with Fusion1. Cost: 20", mouse_pos, font)
        elif BoosterTower_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(surface, "Booster Tower: Boosts towers around by 20%. Cost: 15", mouse_pos, font)

        pygame.display.flip()
        clock.tick(60)

# Outside the loops
pygame.quit()
