import pygame
import math
import sys
from pathlib import Path

pygame.init()
font = pygame.font.SysFont(None, 30)

game_dir = Path(__file__).parent

# Screen setup
screen = pygame.display.set_mode((900, 700))
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
    #init for all block varibales
    def __init__(self, path, speed, color, size, health):
        self.path = path
        self.current_target = 0
        self.x, self.y = self.path[self.current_target]
        self.speed = speed
        self.color = color
        self.size = size
        self.health = health
        self.max_health = health
        self.alive = True
        self.poisoned = False
        self.poison_ticks = 0
        self.last_poison_time = 0
    #Puts the block on screen
    def render(self):
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))
            bar_width = self.size
            bar_height = 5
            bar_x = self.x
            bar_y = self.y - bar_height - 2
            pygame.draw.rect(screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            health_ratio = self.health / self.max_health
            health_color = (int(255 * (1 - health_ratio)), int(255 * health_ratio), 0)
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, bar_width * health_ratio, bar_height))
    #Unused
    def apply_poison(self):
        self.poisoned = True
        self.poison_ticks = 100
        self.last_poison_time = pygame.time.get_ticks()


    #Having it move
    def move(self):
        if not self.alive:
            return False
        target_x, target_y = self.path[self.current_target]
        dx, dy = target_x - self.x, target_y - self.y
        distance = math.hypot(dx, dy)
        if distance < self.speed:
            self.x, self.y = target_x, target_y
            if self.current_target < len(self.path) - 1:
                self.current_target += 1
            else:
                self.alive = False
                return True
        else:
            self.x += self.speed * (dx / distance)
            self.y += self.speed * (dy / distance)
        return False

        if self.poisoned:
            now = pygame.time.get_ticks()
            if now - self.last_poison_time >= 1000:
                self.health -= 1
                self.poison_ticks -= 1
                self.last_poison_time = now
                if self.poison_ticks <= 0:
                    self.poisoned = False

        return False

    #The hitbox
    def get_hitbox(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

#Passing all of the block stuff to the other three
class Block2(Block):
    pass

class Block_small(Block):
    pass

class Block_large(Block):
    pass

# === Tower and Bullet ===
class Rect:
    #init all varibales
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.bullets = []
        self.fire_interval = 2000
        self.last_fire_time = pygame.time.get_ticks()

    #Showing the tower on screen
    def render(self, block=None):
        if block:
            dx = block.x - self.x
            dy = block.y - self.y
            angle = math.atan2(dy, dx)
            half_size = self.size // 2
            rect_points = [(-half_size, -half_size), (half_size, -half_size),
                           (half_size, half_size), (-half_size, half_size)]
            rotated_points = []
            for point in rect_points:
                x, y = point
                rotated_x = x * math.cos(angle) - y * math.sin(angle)
                rotated_y = x * math.sin(angle) + y * math.cos(angle)
                rotated_points.append((self.x + rotated_x, self.y + rotated_y))
            pygame.draw.polygon(screen, self.color, rotated_points)
        else:
            pygame.draw.rect(screen, self.color, (self.x - self.size // 2,
                                                  self.y - self.size // 2,
                                                  self.size, self.size))
    #Firing the bullet
    def fire_bullet(self, block):
        if block is None:
            return  # Don't fire if there's no target

        dx = block.x - self.x
        dy = block.y - self.y
        angle = math.atan2(dy, dx)
        speed = 3
        self.bullets.append(Bullet(self.x, self.y, speed, (0, 0, 0), 10, angle))

    #Updating every frame
    def update(self, current_time):
        global Gold

        # Fire logic
        if current_time - self.last_fire_time > self.fire_interval:
            target_block = next((block for block in blocks if block.alive), None)
            if target_block:
                self.fire_bullet(target_block)
                self.last_fire_time = current_time

        # Bullet updates and collisions
        for bullet in self.bullets[:]:
            bullet.move()
            bullet.render()
            hit = False

            for block_list, gold_reward in [(blocks, 10), (blocks3, 5), (blocks4, 20)]:
                for block in block_list:
                    if block.alive and bullet.get_hitbox().colliderect(block.get_hitbox()):
                        self.bullets.remove(bullet)
                        block.health -= 3
                        if block.health <= 0:
                            block.alive = False
                            Gold += gold_reward
                        hit = True
                        break
                if hit:
                    break
#This class makes money
class money_maker:
    def __init__(self,x , y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.money_interval = 3000
        self.last_money_time = pygame.time.get_ticks()

    def render(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

    def update(self, current_time):
        global Gold
        if current_time - self.last_money_time > self.money_interval:
            Gold += 5
            self.last_money_time = current_time
#The bullets
class Bullet:
    def __init__(self, x, y, speed, color, size, angle):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size  # Diameter
        self.radius = size // 2
        self.angle = angle
        self.hit = False  # Optional: to track collision state

    def render(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def move(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

    def get_hitbox(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

    def hit_target(self):
        self.hit = True


class BoosterTower:
    def __init__(self, x, y, color, size):
        self.name = "booster"
        self.x = x
        self.y = y
        self.size = size
        self.range = 100
        self.boost_applied = False
        self.damage = 0  # Booster itself doesn't shoot
        self.image = pygame.Surface((40, 40))
        self.image.fill((0, 255, 255))  # Cyan color
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.bullets = []
        self.last_fire_time = 0
        self.fire_interval = 1000
        

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        # Optional: draw range circle
        pygame.draw.circle(surface, (0, 255, 255), (self.x, self.y), self.range, 1)

    def apply_boost(self, towers):
        if self.boost_applied:
            return
        for tower in towers:
            if tower is not self and hasattr(tower, 'damage') and tower.damage > 0:
                dist = ((self.x - tower.x) ** 2 + (self.y - tower.y) ** 2) ** 0.5
                if dist <= self.range:
                    tower.damage = int(tower.damage * 1.2)
        self.boost_applied = True

    def render(self, surface):
        surface.blit(self.image, self.rect)
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.range, 1)



#The fusion class
class fusion1:
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.bullets = []
        self.fire_interval = 2000
        self.last_fire_time = pygame.time.get_ticks()

    def render(self, block=None):
        if block:
            dx = block.x - self.x
            dy = block.y - self.y
            angle = math.atan2(dy, dx)
            half_size = self.size // 2
            rect_points = [(-half_size, -half_size), (half_size, -half_size),
                           (half_size, half_size), (-half_size, half_size)]
            rotated_points = []
            for point in rect_points:
                x, y = point
                rotated_x = x * math.cos(angle) - y * math.sin(angle)
                rotated_y = x * math.sin(angle) + y * math.cos(angle)
                rotated_points.append((self.x + rotated_x, self.y + rotated_y))
            pygame.draw.polygon(screen, self.color, rotated_points)
        else:
            pygame.draw.rect(screen, self.color, (self.x - self.size // 2,
                                                  self.y - self.size // 2,
                                                  self.size, self.size))

    def fire_bullet(self, block):
        if block is None:
            return  # Don't fire if there's no target

        dx = block.x - self.x
        dy = block.y - self.y
        angle = math.atan2(dy, dx)
        speed = 3
        self.bullets.append(Bullet(self.x, self.y, speed, (0, 0, 0), 10, angle))

    def update(self, current_time):
        global Gold

        # Fire logic
        if current_time - self.last_fire_time > self.fire_interval:
            target_block = next((block for block in blocks if block.alive), None)
            if target_block:
                self.fire_bullet(target_block)
                self.last_fire_time = current_time

        # Bullet updates and collisions
        for bullet in self.bullets[:]:
            bullet.move()
            bullet.render()
            hit = False

            for block_list, gold_reward in [(blocks, 10), (blocks3, 5), (blocks4, 20)]:
                for block in block_list:
                    if block.alive and bullet.get_hitbox().colliderect(block.get_hitbox()):
                        self.bullets.remove(bullet)
                        block.health -= 3
                        if block.health <= 0:
                            block.alive = False
                            Gold += gold_reward
                        hit = True
                        break
                if hit:
                    break
class fusion2:
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.bullets = []
        self.fire_interval = 2000
        self.last_fire_time = pygame.time.get_ticks()

    def render(self, block=None):
        if block:
            dx = block.x - self.x
            dy = block.y - self.y
            angle = math.atan2(dy, dx)
            half_size = self.size // 2
            rect_points = [(-half_size, -half_size), (half_size, -half_size),
                           (half_size, half_size), (-half_size, half_size)]
            rotated_points = []
            for point in rect_points:
                x, y = point
                rotated_x = x * math.cos(angle) - y * math.sin(angle)
                rotated_y = x * math.sin(angle) + y * math.cos(angle)
                rotated_points.append((self.x + rotated_x, self.y + rotated_y))
            pygame.draw.polygon(screen, self.color, rotated_points)
        else:
            pygame.draw.rect(screen, self.color, (self.x - self.size // 2,
                                                  self.y - self.size // 2,
                                                  self.size, self.size))

    def fire_bullet(self, block):
        if block is None:
            return  # Don't fire if there's no target

        dx = block.x - self.x
        dy = block.y - self.y
        angle = math.atan2(dy, dx)
        speed = 3
        self.bullets.append(Bullet(self.x, self.y, speed, (0, 0, 0), 10, angle))

    def update(self, current_time):
        global Gold

        # Fire logic
        if current_time - self.last_fire_time > self.fire_interval:
            target_block = next((block for block in blocks if block.alive), None)
            if target_block:
                self.fire_bullet(target_block)
                self.last_fire_time = current_time

        # Bullet updates and collisions
        for bullet in self.bullets[:]:
            bullet.move()
            bullet.render()
            hit = False

            for block_list, gold_reward in [(blocks, 10), (blocks3, 5), (blocks4, 20)]:
                for block in block_list:
                    if block.alive and bullet.get_hitbox().colliderect(block.get_hitbox()):
                        self.bullets.remove(bullet)
                        block.health -= 3
                        if block.health <= 0:
                            block.alive = False
                            Gold += gold_reward
                        hit = True
                        break
                if hit:
                    break
#What happens when you fuse the two fusion towers two gather                   
class fused:
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.bullets = []
        self.fire_interval = 2000
        self.last_fire_time = pygame.time.get_ticks()
        self.money_interval = 5000
        self.last_money_time = pygame.time.get_ticks()

    def render(self, block=None):
        if block:
            dx = block.x - self.x
            dy = block.y - self.y
            angle = math.atan2(dy, dx)
            half_size = self.size // 2
            rect_points = [(-half_size, -half_size), (half_size, -half_size),
                           (half_size, half_size), (-half_size, half_size)]
            rotated_points = []
            for point in rect_points:
                x, y = point
                rotated_x = x * math.cos(angle) - y * math.sin(angle)
                rotated_y = x * math.sin(angle) + y * math.cos(angle)
                rotated_points.append((self.x + rotated_x, self.y + rotated_y))
            pygame.draw.polygon(screen, self.color, rotated_points)
        else:
            pygame.draw.rect(screen, self.color, (self.x - self.size // 2,
                                                  self.y - self.size // 2,
                                                  self.size, self.size))

    def fire_bullet(self, block):
        if block is None:
            return  # Don't fire if there's no target

        dx = block.x - self.x
        dy = block.y - self.y
        angle = math.atan2(dy, dx)
        speed = 3
        self.bullets.append(Bullet(self.x, self.y, speed, (0, 0, 0), 10, angle))

    def update(self, current_time):
        global Gold

        # Fire logic
        if current_time - self.last_fire_time > self.fire_interval:
            target_block = next((block for block in blocks if block.alive), None)
            if target_block:
                self.fire_bullet(target_block)
                self.last_fire_time = current_time

        # Bullet updates and collisions
        for bullet in self.bullets[:]:
            bullet.move()
            bullet.render()
            hit = False

            for block_list, gold_reward in [(blocks, 10), (blocks3, 5), (blocks4, 20)]:
                for block in block_list:
                    if block.alive and bullet.get_hitbox().colliderect(block.get_hitbox()):
                        self.bullets.remove(bullet)
                        block.health -= 3
                        if block.health <= 0:
                            block.alive = False
                            Gold += gold_reward
                        hit = True
                        break
                if hit:
                    break

    def update_money(self, current_time):
        global Gold
        if current_time - self.last_money_time > self.money_interval:
            Gold += 7
            self.last_money_time = current_time




#Reset the game
def reset_game():
    global Gold, placed_towers, placed_money_towers, placed_fusion1, placed_fusion2, made_fusion
    global blocks, blocks2, blocks3, blocks4
    global player_base_health, spawn_time_1, spawn_time_2, spawn_time_3, spawn_time_4
    global dragging_tower, dragging_money, dragging_fusion1, dragging_fusion2, dragging_Posion

    Gold = 10
    player_base_health = 10
    spawn_time_1 = spawn_time_2 = spawn_time_3 = spawn_time_4 = pygame.time.get_ticks()

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

    dragging_tower = dragging_money = dragging_fusion1 = dragging_fusion2 = dragging_Posion = False





# === Menu ===
class Menu:
    def __init__(self, x, y, color, width, height):
        self.x = x
        self.y = y
        self.color = color
        self.width = width
        self.height = height

    def render(self):
        #Show the icons
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, (255, 0, 0), (self.x + 50, self.y + 50, 40, 40))  # tower icon
        pygame.draw.rect(screen, (255, 215, 0), (self.x + 100, self.y + 50, 40, 40))  # money icon
        pygame.draw.rect(screen, (255, 100, 50), (self.x + 50, self.y + 100, 40, 40))  # fusion1 icon
        pygame.draw.rect(screen, (50, 100, 50), (self.x + 100, self.y + 100, 40, 40))  # fusion2 icon
        pygame.draw.rect(screen, (0, 0, 255), (self.x + 50, self.y + 150, 40, 40))  # Boostertower icon

# === Game Setup ===
path = [(0, 50), (450, 50), (450, 450), (0, 450)]

rect = Rect(200, 200, (255, 0, 0), 40)
menu_panel = Menu(700, 0, (50, 50, 50), 200, 700)

blocks = []
blocks2 = []
blocks3 = []
blocks4 = []
spawn_time_1 = spawn_time_2 = spawn_time_3 = spawn_time_4 = pygame.time.get_ticks()

player_base_health = 10
Gold = 10
dragging_tower = False
dragging_money = False
dragging_fusion1 = False
dragging_fusion2 = False
dragging_BoosterTower = False
placed_towers = []
placed_money_towers = []
placed_fusion1 = []
placed_fusion2 = []
made_fusion = []
placed_BoosterTower = []
towers = []

#Icon hitbox
tower_icon_rect = pygame.Rect(menu_panel.x + 50, menu_panel.y + 50, 40, 40)
money_icon_rect = pygame.Rect(menu_panel.x + 100, menu_panel.y + 50, 40, 40)
fusion1_icon_rect = pygame.Rect(menu_panel.x + 50, menu_panel.y + 100, 40, 40)
fusion2_icon_rect = pygame.Rect(menu_panel.x + 100, menu_panel.y + 100, 40, 40)
BoosterTower_icon_rect = pygame.Rect(menu_panel.x + 50, menu_panel.y + 150, 40, 40)


# === Game Loop ===
while True:
    reset_game()
    running = True
    while running:
        # === HANDLE EVENTS ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            #What happens when you click on the icons
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

                # Avoid placing on path
                path_width = 30
                for i in range(len(path) - 1):
                    start, end = path[i], path[i + 1]
                    line_rect = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                                            abs(start[0] - end[0]) or 1, abs(start[1] - end[1]) or 1)
                    line_rect.inflate_ip(path_width, path_width)
                    if tower_rect.colliderect(line_rect):
                        valid_placement = False
                        break

                # Avoid overlap with all existing towers (including fused towers)
                all_existing_towers = (
                    placed_towers + placed_money_towers + placed_fusion1 +
                    placed_fusion2 + made_fusion + placed_BoosterTower
                )
                for turret in all_existing_towers:
                    existing_rect = pygame.Rect(turret.x - turret.size // 2, turret.y - turret.size // 2, turret.size, turret.size)
                    if tower_rect.colliderect(existing_rect):
                        valid_placement = False
                        break

                # === HANDLE TOWER PLACEMENT ===
                if dragging_tower and Gold >= 3 and valid_placement and x < menu_panel.x:
                    placed_towers.append(Rect(x, y, (255, 0, 0), 40))
                    Gold -= 3

                elif dragging_money and Gold >= 7 and valid_placement and x < menu_panel.x:
                    placed_money_towers.append(money_maker(x, y, (255, 215, 0), 40))
                    Gold -= 7

                
                elif dragging_BoosterTower and Gold >= 1 and valid_placement and x < menu_panel.x:
                    placed_BoosterTower.append(BoosterTower(x, y, (0, 0, 255), 40))
                    Gold -= 1
                    
                elif dragging_fusion1 and Gold >= 12 and x < menu_panel.x:
                    fusion_rect = pygame.Rect(x - 20, y - 20, 40, 40)
                    fusion2_found = None
                    for turret in placed_fusion2:
                        existing_rect = pygame.Rect(turret.x - turret.size // 2, turret.y - turret.size // 2, turret.size, turret.size)
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

                elif dragging_fusion2 and Gold >= 20 and x < menu_panel.x:
                    fusion_rect = pygame.Rect(x - 20, y - 20, 40, 40)
                    fusion1_found = None
                    for turret in placed_fusion1:
                        existing_rect = pygame.Rect(turret.x - turret.size // 2, turret.y - turret.size // 2, turret.size, turret.size)
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

                dragging_tower = dragging_money = dragging_fusion1 = dragging_fusion2 = dragging_Posion = False

        # === HANDLE KEYS ===
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            running = False

        



        # === DRAW ===
        screen.fill((255, 255, 255))
        current_time = pygame.time.get_ticks()
        pygame.draw.lines(screen, (200, 200, 200), False, path, 2)
        menu_panel.render()

        # === GOLD UI ===
        coin_x, coin_y, coin_radius = menu_panel.x + 25, menu_panel.y + 20, 12
        pygame.draw.circle(screen, (218, 165, 32), (coin_x, coin_y), coin_radius)
        pygame.draw.circle(screen, (184, 134, 11), (coin_x, coin_y), coin_radius, 2)
        pygame.draw.arc(screen, (255, 255, 255), (coin_x - 8, coin_y - 8, 16, 16), math.pi * 0.25, math.pi * 0.75, 2)
        gold_text = font.render(f"{Gold}", True, (255, 255, 255))
        gold_rect = gold_text.get_rect(midleft=(coin_x + 20, coin_y))
        screen.blit(gold_text, gold_rect)

        # === DRAGGING PREVIEW ===
        if dragging_tower or dragging_money or dragging_fusion1 or dragging_fusion2 or dragging_BoosterTower:
            mx, my = pygame.mouse.get_pos()
            color = (255, 0, 0) if dragging_tower else \
                    (255, 215, 0) if dragging_money else \
                    (255, 100, 50) if dragging_fusion1 else \
                    (50, 100, 50) if dragging_fusion2 else \
                    (0, 0, 255) if dragging_BoosterTower else \
                    (0, 0, 255)
            pygame.draw.rect(screen, color, (mx - 20, my - 20, 40, 40))

        # === SPAWN ENEMIES ===
        if current_time - spawn_time_1 > 5000:
            blocks.append(Block(path, 0.4, (0, 0, 0), 25, 2))
            spawn_time_1 = current_time
        if current_time - spawn_time_2 > 10000:
            blocks4.append(Block_large(path, 0.2, (255, 0, 0), 50, 3))
            spawn_time_2 = current_time
        if current_time - spawn_time_3 > 3000:
            blocks3.append(Block_small(path, 0.6, (0, 0, 255), 10, 1))
            spawn_time_3 = current_time
        if current_time - spawn_time_4 > 20000:
            blocks2.append(Block2(path, 0.8, (0, 100, 26), 30, 2))
            spawn_time_4 = current_time

        # === ENEMY MOVEMENT ===
        for group, health_loss in zip([blocks, blocks2, blocks3, blocks4], [2, 3, 1, 5]):
            for block in group[:]:
                reached = block.move()
                block.render()
                if not block.alive:
                    group.remove(block)
                    if reached:
                        player_base_health -= health_loss

        # === TARGETS SETUP ===
        targets = [
            (next((b for b in blocks if b.alive), None), blocks, 2),
            (next((b for b in blocks3 if b.alive), None), blocks3, 1),
            (next((b for b in blocks4 if b.alive), None), blocks4, 4)
        ]

        all_turret_groups = [
            (placed_towers, 1, 1),
            (placed_fusion1, 1, 2),
            (placed_fusion2, 3, 1),
            (made_fusion, 5, 3),
            (placed_BoosterTower, 0, 0)
        ]

        # === TOWER FIRING ===
        for turrets, multiplier, block_d in all_turret_groups:
            for turret in turrets:
                if isinstance(turret, BoosterTower):
                    continue
                
                for target, _, _ in targets:
                    turret.render(target)
                    
                for target, _, _ in targets:
                    if target and current_time - turret.last_fire_time > turret.fire_interval:
                        if getattr(turret, "is_poison", False):
                            turret.fire_poison_bullet(target)
                        else:
                            turret.fire_bullet(target)
                        turret.last_fire_time = current_time

                bullets_to_remove = []
                Gold_to_add = 0  # to avoid modifying Gold inside loop if needed

                for bullet in turret.bullets[:]:
                    bullet.move()
                    bullet.render(screen)
                    
                    hit_something = False
                    
                    # Check hit on enemies (targets)
                    for enemy in targets:
                        if bullet.hit_target(enemy):
                            enemy.take_damage(bullet.damage)
                            hit_something = True
                            break  # bullet hit an enemy, stop checking
                    
                    # Check hit on blocks if bullet hasn't already hit enemy
                    if not hit_something:
                        for target, block_group, gold_reward in targets:
                            for block in block_group:
                                if block.alive:
                                    bullet_rect = pygame.Rect(
                                        bullet.x - bullet.radius,
                                        bullet.y - bullet.radius,
                                        bullet.radius * 2,
                                        bullet.radius * 2,
                                    )
                                    if bullet_rect.colliderect(block.get_hitbox()):
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

                # Remove bullets only once after processing all collisions
                for bullet in bullets_to_remove:
                    if bullet in turret.bullets:
                        turret.bullets.remove(bullet)

                # Add gold after processing
                Gold += Gold_to_add


        # === MONEY GENERATION ===
        for m in placed_money_towers:
            m.render()
            m.update(current_time)
        for n in made_fusion:
            n.render()
            n.update_money(current_time)

        # === Boosting ===
        for booster in placed_BoosterTower:
            booster.draw(screen)
            booster.apply_boost(placed_towers + placed_fusion1 + placed_fusion2 + made_fusion)



        # === BASE HEALTH BAR ===
        pygame.draw.rect(screen, (150, 150, 150), (10, 10, 200, 20))
        pygame.draw.rect(screen, (0, 200, 0), (10, 10, 200 * (player_base_health / 10), 20))

        # === GAME OVER ===
        if player_base_health <= 0:
            screen.blit(pygame.font.SysFont(None, 50).render("Game Over", True, (255, 0, 0)), (350, 300))
            pygame.display.flip()
            pygame.time.delay(3000)
            running = False# === GAME OVER ===
            if player_base_health <= 0:
                screen.blit(pygame.font.SysFont(None, 50).render("Game Over", True, (255, 0, 0)), (350, 300))
                screen.blit(pygame.font.SysFont(None, 36).render("Press R to Play Again or ESC to Quit", True, (0, 0, 0)), (250, 350))
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
                                running = False  # end current game loop, restart from top
                            elif event.key == pygame.K_ESCAPE:
                                pygame.quit()
                                sys.exit()
                break  # exit current game loop

        mouse_pos = pygame.mouse.get_pos()

        if tower_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(screen, "Basic Tower: Shoots at enemies. Cost:3", mouse_pos, font)
        elif money_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(screen, "Money Tower: Generates gold over time. Cost: 7", mouse_pos, font)
        elif fusion1_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(screen, "Fusion1 Tower: Shoots more powerful bullets. Can be combined with Fusion2. Cost: 12", mouse_pos, font)
        elif fusion2_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(screen, "Fusion2 Tower: Shoots slower but generates money over time. Can be combined with Fusion1. Cost: 20", mouse_pos, font)
        elif BoosterTower_icon_rect.collidepoint(mouse_pos):
            draw_tooltip(screen, "Booster Tower: Can boosts towers around it by 20%. Cost: 15", mouse_pos, font)


        pygame.display.flip()
        clock.tick(60)

pygame.display.update()
pygame.quit()
