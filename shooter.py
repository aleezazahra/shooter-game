import os
import glob
import pygame
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter Game")
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.55
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRENADE_FUSE = 100
GRENADE_DAMAGE = 30
GRENADE_RADIUS = 60
TILE_SIZE = 40
ROWS = SCREEN_HEIGHT // TILE_SIZE
ENEMY_SHOOT_RANGE = 500
ENEMY_CHASE_RANGE = 350
ENEMY_SHOOT_COOLDOWN = 90

STATE_START = "start"
STATE_PLAYING = "playing"
STATE_LEVEL_COMPLETE = "level_complete"
STATE_GAME_OVER = "game_over"
STATE_WIN = "win"
game_state = STATE_START

moving_left = False
moving_right = False
shoot = False
grenade_key_down = False
grenade_thrown = False

scroll_x = 0
level_width = SCREEN_WIDTH
exit_x = SCREEN_WIDTH
current_tiles = []
current_level_index = 0
transition_timer = 0


def sorted_image_paths(folder):
    paths = glob.glob(os.path.join(folder, "*.png"))

    def sort_key(path):
        stem = os.path.splitext(os.path.basename(path))[0]
        return (0, int(stem)) if stem.isdigit() else (1, stem)

    return sorted(paths, key=sort_key)


bullet_img = pygame.image.load(os.path.join(BASE_DIR, "img", "icons", "bullet.png")).convert_alpha()
grenade_img = pygame.image.load(os.path.join(BASE_DIR, "img", "icons", "grenade.png")).convert_alpha()
health_box_img = pygame.image.load(os.path.join(BASE_DIR, "img", "icons", "health_box.png")).convert_alpha()
ammo_box_img = pygame.image.load(os.path.join(BASE_DIR, "img", "icons", "ammo_box.png")).convert_alpha()
grenade_box_img = pygame.image.load(os.path.join(BASE_DIR, "img", "icons", "grenade_box.png")).convert_alpha()

item_boxes = {
    'Health': health_box_img,
    'Ammo': ammo_box_img,
    'Grenade': grenade_box_img
}


def load_tile_images():
    folder = os.path.join(BASE_DIR, "img", "tile")
    images = []
    for path in sorted_image_paths(folder):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        images.append(img)
    if not images:
        fallback = pygame.Surface((TILE_SIZE, TILE_SIZE))
        fallback.fill((120, 72, 42))
        images.append(fallback)
    return images


def load_background_layers():
    folder = os.path.join(BASE_DIR, "img", "background")
    layers = []
    for path in sorted_image_paths(folder):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        layers.append(img)
    if not layers:
        fallback = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fallback.fill((92, 62, 110))
        layers.append(fallback)
    return layers


def load_button_image(filename, target_width=220):
    path = os.path.join(BASE_DIR, "img", filename)
    img = pygame.image.load(path).convert_alpha()
    ratio = target_width / img.get_width()
    img = pygame.transform.smoothscale(img, (target_width, int(img.get_height() * ratio)))
    return img


tile_images = load_tile_images()
background_layers = load_background_layers()
start_btn_img = load_button_image("start_btn.png")
restart_btn_img = load_button_image("restart_btn.png")
exit_btn_img = load_button_image("exit_btn.png")


font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 64)

RED = (230, 60, 60)
WHITE = (240, 240, 245)
BLACK = (0, 0, 0)
GREEN = (90, 210, 130)
ORANGE = (255, 140, 0)
GOLD = (230, 180, 90)
HUD_BG = (15, 15, 25, 160)

animation_cache = {}
explosion_frames_cache = None


def draw_bg():
    for layer in background_layers:
        screen.blit(layer, (0, 0))


def draw_text(text, x, y, color=WHITE, use_font=font):
    img = use_font.render(text, True, color)
    screen.blit(img, (x, y))


def draw_hud_panel(x, y, width, height):
    panel = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(panel, HUD_BG, (0, 0, width, height), border_radius=10)
    screen.blit(panel, (x, y))


def draw_health_bar(x, y, health, max_health):
    ratio = max(health, 0) / max_health
    pygame.draw.rect(screen, BLACK, (x - 2, y - 2, 154, 24), border_radius=4)
    pygame.draw.rect(screen, (70, 20, 20), (x, y, 150, 20), border_radius=3)
    pygame.draw.rect(screen, GREEN, (x, y, 150 * ratio, 20), border_radius=3)


def load_soldier_animations(char_type, scale):
    cache_key = (char_type, scale)
    if cache_key in animation_cache:
        return animation_cache[cache_key]

    animation_list = []
    animation_types = ['Idle', 'Run', 'Jump', 'Death']
    for animation in animation_types:
        temp_list = []
        folder = os.path.join(BASE_DIR, "img", char_type, animation)
        found_files = glob.glob(os.path.join(folder, "*.png"))
        frame_numbers = []
        for path in found_files:
            name = os.path.splitext(os.path.basename(path))[0]
            if name.isdigit():
                frame_numbers.append(int(name))
        frame_numbers.sort()

        if not frame_numbers:
            print(f"Missing animation folder or frames: {folder}")
            frame_numbers = [0]

        for i in frame_numbers:
            img_path = os.path.join(folder, f"{i}.png")
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(
                img, (int(img.get_width() * scale), int(img.get_height() * scale))
            )
            temp_list.append(img)

        animation_list.append(temp_list)

    animation_cache[cache_key] = animation_list
    return animation_list


def load_explosion_frames(scale=0.5, radius=GRENADE_RADIUS):
    global explosion_frames_cache
    if explosion_frames_cache is not None:
        return explosion_frames_cache

    frames = []
    for num in range(1, 6):
        img_path = os.path.join(BASE_DIR, "img", "explosion", f"exp{num}.png")
        if os.path.exists(img_path):
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(
                img, (int(img.get_width() * scale), int(img.get_height() * scale))
            )
        else:
            size = int(radius * 2 * (0.4 + num * 0.15))
            img = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(img, ORANGE, (size // 2, size // 2), size // 2)
        frames.append(img)

    explosion_frames_cache = frames
    return frames


class Tile:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)


def build_level(config):
    cols = len(config['ground'])
    width = cols * TILE_SIZE
    tiles = []
    tile_img = tile_images[0]

    for col, top_row in enumerate(config['ground']):
        if top_row < 0:
            continue
        for row in range(top_row, ROWS):
            tiles.append(Tile(tile_img, col * TILE_SIZE, row * TILE_SIZE))

    for row, col_start, length in config.get('platforms', []):
        for i in range(length):
            col = col_start + i
            tiles.append(Tile(tile_img, col * TILE_SIZE, row * TILE_SIZE))

    return tiles, width


LEVELS = [
    {
        'ground': [10, 10, 10, 10, -1, -1, -1, 13, 13, 13, 13, 13, -1, -1, 12, 12, 12, 12, -1, -1, -1,
                   14, 14, 14, 14, -1, -1, 14, 14, 14],
        'platforms': [(9, 4, 3), (11, 12, 2), (11, 18, 3)],
        'player_spawn': (80, 400),
        'enemies': [(380, 520), (660, 480), (940, 560)],
        'items': [('Health', 100, 400), ('Ammo', 340, 520), ('Grenade', 620, 480)],
    },
    {
        'ground': [12, 12, 12, 12, -1, -1, -1, 13, 13, 13, -1, -1, 12, 12, 12, 12, -1, -1, -1,
                   11, 11, 11, -1, -1, 12, 12, 12, 12, 12, 12],
        'platforms': [(11, 4, 3), (11, 10, 2), (10, 16, 3), (10, 22, 2)],
        'player_spawn': (80, 480),
        'enemies': [(340, 520), (540, 480), (820, 440), (1060, 480)],
        'items': [('Health', 100, 480), ('Grenade', 380, 520), ('Ammo', 580, 480), ('Ammo', 1020, 480)],
    },
]


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades=3, is_ai=False):
        super().__init__()
        self.alive = True
        self.jump = False
        self.in_air = False
        self.char_type = char_type
        self.is_ai = is_ai
        self.health = 100
        self.max_health = 100
        self.shoot_cooldown = 0
        self.speed = speed
        self.direction = 1
        self.flip = False
        self.vel_y = 0
        self.ammo = ammo
        self.start_ammo = ammo
        self.grenades = grenades
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        self.animation_list = load_soldier_animations(char_type, scale)
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)

    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right, world_tiles):
        dx = 0
        dy = 0

        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1

        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        if self.jump and not self.in_air:
            self.vel_y = -13
            self.jump = False
            self.in_air = True

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        self.rect.x += dx
        for tile in world_tiles:
            if tile.rect.colliderect(self.rect):
                if dx > 0:
                    self.rect.right = tile.rect.left
                elif dx < 0:
                    self.rect.left = tile.rect.right

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > level_width:
            self.rect.right = level_width

        self.rect.y += dy
        self.in_air = True
        for tile in world_tiles:
            if tile.rect.colliderect(self.rect):
                if dy > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel_y = 0
                    self.in_air = False
                elif dy < 0:
                    self.rect.top = tile.rect.bottom
                    self.vel_y = 0

        if self.rect.top > SCREEN_HEIGHT:
            self.health = 0

    def shoot(self):
        if self.alive and self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(
                self.rect.centerx + (0.6 * self.rect.width * self.direction),
                self.rect.centery,
                self.direction,
                self,
            )
            bullet_group.add(bullet)
            self.ammo -= 1

    def throw_grenade(self):
        if self.alive and self.grenades > 0:
            grenade = Grenade(
                self.rect.centerx + (0.5 * self.rect.width * self.direction),
                self.rect.top,
                self.direction,
                self,
            )
            grenade_group.add(grenade)
            self.grenades -= 1

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        old_midbottom = self.rect.midbottom
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect(midbottom=old_midbottom)

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - scroll_x, self.rect.y))


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        super().__init__()
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)

    def update(self):
        if pygame.sprite.collide_rect(self, player):
            if self.item_type == "Health":
                player.health = min(player.health + 25, player.max_health)
            elif self.item_type == "Ammo":
                player.ammo += 15
            elif self.item_type == "Grenade":
                player.grenades += 3
            self.kill()

    def draw(self):
        screen.blit(self.image, (self.rect.x - scroll_x, self.rect.y))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, owner):
        super().__init__()
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.owner = owner

    def update(self):
        self.rect.x += (self.direction * self.speed)
        if self.rect.right < 0 or self.rect.left > level_width:
            self.kill()
            return

        hits = pygame.sprite.spritecollide(self, characters, False)
        for target in hits:
            if target is self.owner or not target.alive:
                continue
            target.health -= 5
            self.kill()
            break

    def draw(self):
        screen.blit(self.image, (self.rect.x - scroll_x, self.rect.y))


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, owner):
        super().__init__()
        self.timer = GRENADE_FUSE
        self.vel_y = -11
        self.speed = 7
        self.direction = direction
        self.owner = owner
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10

        dx = self.direction * self.speed
        dy = self.vel_y

        self.rect.x += dx
        if self.rect.left < 0 or self.rect.right > level_width:
            self.rect.x -= dx
            self.direction *= -1

        self.rect.y += dy
        for tile in current_tiles:
            if tile.rect.colliderect(self.rect):
                if dy > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel_y = -self.vel_y * 0.6
                    self.speed *= 0.8
                break

        self.timer -= 1
        if self.timer <= 0:
            self.explode()

    def explode(self):
        for target in characters:
            if not target.alive or target is self.owner:
                continue
            distance = ((target.rect.centerx - self.rect.centerx) ** 2 +
                        (target.rect.centery - self.rect.centery) ** 2) ** 0.5
            if distance <= GRENADE_RADIUS:
                falloff = 1 - (distance / GRENADE_RADIUS) * 0.5
                target.health -= GRENADE_DAMAGE * falloff

        explosion = Explosion(self.rect.centerx, self.rect.centery, 0.5)
        explosion_group.add(explosion)
        self.kill()

    def draw(self):
        screen.blit(self.image, (self.rect.x - scroll_x, self.rect.y))


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        super().__init__()
        self.images = load_explosion_frames(scale)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0
        self.animation_speed = 4

    def update(self):
        self.counter += 1
        if self.counter >= self.animation_speed:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.index]
                self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self):
        screen.blit(self.image, (self.rect.x - scroll_x, self.rect.y))


class ImageButton:
    def __init__(self, image, x, y):
        self.base_image = image
        self.hover_image = pygame.transform.smoothscale(
            image, (int(image.get_width() * 1.08), int(image.get_height() * 1.08))
        )
        self.rect = self.base_image.get_rect(center=(x, y))

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            img = self.hover_image
            rect = img.get_rect(center=self.rect.center)
        else:
            img = self.base_image
            rect = self.rect
        screen.blit(img, rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


start_button = ImageButton(start_btn_img, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
restart_button = ImageButton(restart_btn_img, SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 70)
exit_button = ImageButton(exit_btn_img, SCREEN_WIDTH // 2 + 130, SCREEN_HEIGHT // 2 + 70)


def resolve_enemy_overlap(enemy_list):
    for i in range(len(enemy_list)):
        for j in range(i + 1, len(enemy_list)):
            a = enemy_list[i]
            b = enemy_list[j]
            if not a.alive or not b.alive:
                continue
            if a.rect.colliderect(b.rect):
                if a.rect.centerx <= b.rect.centerx:
                    overlap = a.rect.right - b.rect.left
                    push = overlap // 2 + 1
                    a.rect.x -= push
                    b.rect.x += push
                else:
                    overlap = b.rect.right - a.rect.left
                    push = overlap // 2 + 1
                    a.rect.x += push
                    b.rect.x -= push
                a.rect.left = max(a.rect.left, 0)
                a.rect.right = min(a.rect.right, level_width)
                b.rect.left = max(b.rect.left, 0)
                b.rect.right = min(b.rect.right, level_width)


def enemy_ai(enemy, player, world_tiles):
    if not enemy.alive:
        return

    if not player.alive:
        enemy.update_action(0)
        return

    dx = player.rect.centerx - enemy.rect.centerx
    distance = abs(dx)

    enemy.direction = 1 if dx > 0 else -1
    enemy.flip = enemy.direction == -1

    if distance <= ENEMY_SHOOT_RANGE:
        enemy.update_action(0)
        if enemy.shoot_cooldown == 0 and enemy.ammo > 0:
            enemy.shoot()
            enemy.shoot_cooldown = ENEMY_SHOOT_COOLDOWN
        if distance > ENEMY_CHASE_RANGE:
            moving_toward_left = enemy.direction == -1
            moving_toward_right = enemy.direction == 1
            enemy.update_action(1)
            enemy.move(moving_toward_left, moving_toward_right, world_tiles)
    else:
        moving_toward_left = enemy.direction == -1
        moving_toward_right = enemy.direction == 1
        enemy.update_action(1)
        enemy.move(moving_toward_left, moving_toward_right, world_tiles)


bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
characters = pygame.sprite.Group()
player = None
enemy_list = []


def start_level(index):
    global player, enemy_list, current_tiles, level_width, exit_x, game_state
    global moving_left, moving_right, shoot, grenade_key_down, grenade_thrown
    global current_level_index, scroll_x

    current_level_index = index
    config = LEVELS[index]
    current_tiles, level_width = build_level(config)
    exit_x = level_width - TILE_SIZE * 3

    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    characters.empty()

    for item_type, x, y in config['items']:
        item_box_group.add(ItemBox(item_type, x, y))

    saved_ammo = player.ammo if player else 20
    saved_grenades = player.grenades if player else 3

    px, py = config['player_spawn']
    player = Soldier('player', px, py, 3.0, 6, saved_ammo, saved_grenades)
    characters.add(player)

    enemy_list = []
    for ex, ey in config['enemies']:
        enemy = Soldier('enemy', ex, ey, 3.0, 3, 20, is_ai=True)
        enemy_list.append(enemy)
        characters.add(enemy)

    scroll_x = 0
    moving_left = False
    moving_right = False
    shoot = False
    grenade_key_down = False
    grenade_thrown = False
    game_state = STATE_PLAYING


def restart_game():
    global player
    player = None
    start_level(0)


run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if game_state == STATE_PLAYING:
                if event.key == pygame.K_a and player.alive:
                    moving_left = True
                if event.key == pygame.K_d and player.alive:
                    moving_right = True
                if event.key == pygame.K_w and player.alive:
                    player.jump = True
                if event.key == pygame.K_SPACE:
                    shoot = True
                if event.key == pygame.K_q:
                    grenade_key_down = True
            if event.key == pygame.K_ESCAPE:
                run = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q:
                grenade_key_down = False
                grenade_thrown = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == STATE_START and start_button.is_clicked(event.pos):
                start_level(0)
            elif game_state in (STATE_GAME_OVER, STATE_WIN):
                if restart_button.is_clicked(event.pos):
                    restart_game()
                elif exit_button.is_clicked(event.pos):
                    run = False

    if game_state == STATE_START:
        draw_bg()
        draw_text("SHOOTER", SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT // 2 - 80, WHITE, big_font)
        start_button.draw()

    elif game_state == STATE_PLAYING:
        scroll_x = player.rect.centerx - SCREEN_WIDTH // 2
        scroll_x = max(0, min(scroll_x, level_width - SCREEN_WIDTH))

        draw_bg()

        for tile in current_tiles:
            draw_x = tile.rect.x - scroll_x
            if -TILE_SIZE <= draw_x <= SCREEN_WIDTH:
                screen.blit(tile.image, (draw_x, tile.rect.y))

        exit_draw_x = exit_x - scroll_x
        if -10 <= exit_draw_x <= SCREEN_WIDTH + 10:
            pygame.draw.line(screen, GOLD, (exit_draw_x, 0), (exit_draw_x, SCREEN_HEIGHT), 4)

        for item in item_box_group:
            item.draw()

        draw_hud_panel(4, 4, 220, 100)
        draw_health_bar(14, 14, player.health, player.max_health)
        draw_text(f"AMMO: {player.ammo}", 14, 44)
        draw_text(f"GRENADES: {player.grenades}", 14, 74)

        enemies_alive = sum(1 for e in enemy_list if e.alive)
        draw_hud_panel(SCREEN_WIDTH - 220, 4, 216, 40)
        draw_text(f"LEVEL {current_level_index + 1}  ENEMIES: {enemies_alive}", SCREEN_WIDTH - 208, 14)

        if player.alive:
            if shoot:
                player.shoot()
            if grenade_key_down and not grenade_thrown:
                player.throw_grenade()
                grenade_thrown = True

            if player.in_air:
                player.update_action(2)
            elif moving_left or moving_right:
                player.update_action(1)
            else:
                player.update_action(0)

            player.move(moving_left, moving_right, current_tiles)

        for enemy in enemy_list:
            enemy_ai(enemy, player, current_tiles)

        resolve_enemy_overlap(enemy_list)

        item_box_group.update()

        for character in characters:
            character.update()
            character.draw()

        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        for b in bullet_group:
            b.draw()
        for g in grenade_group:
            g.draw()
        for e in explosion_group:
            e.draw()

        if not player.alive:
            game_state = STATE_GAME_OVER
        elif player.rect.centerx >= exit_x:
            game_state = STATE_LEVEL_COMPLETE
            transition_timer = 90

    elif game_state == STATE_LEVEL_COMPLETE:
        draw_bg()
        for tile in current_tiles:
            draw_x = tile.rect.x - scroll_x
            if -TILE_SIZE <= draw_x <= SCREEN_WIDTH:
                screen.blit(tile.image, (draw_x, tile.rect.y))
        for character in characters:
            character.draw()

        draw_text(f"LEVEL {current_level_index + 1} COMPLETE",
                  SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 20, GOLD, big_font)

        transition_timer -= 1
        if transition_timer <= 0:
            if current_level_index + 1 < len(LEVELS):
                start_level(current_level_index + 1)
            else:
                game_state = STATE_WIN

    else:
        draw_bg()
        for tile in current_tiles:
            draw_x = tile.rect.x - scroll_x
            if -TILE_SIZE <= draw_x <= SCREEN_WIDTH:
                screen.blit(tile.image, (draw_x, tile.rect.y))
        for character in characters:
            character.update()
            character.draw()
        for e in explosion_group:
            e.update()
            e.draw()

        message = "GAME OVER" if game_state == STATE_GAME_OVER else "YOU WIN"
        color = RED if game_state == STATE_GAME_OVER else GREEN
        text_img = big_font.render(message, True, color)
        text_rect = text_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(text_img, text_rect)
        restart_button.draw()
        exit_button.draw()

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()