import os
import pygame

pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter Game")
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.75
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GRENADE_FUSE = 100
GRENADE_DAMAGE = 30
GRENADE_RADIUS = 60
GROUND_Y = 300

ENEMY_COUNT = 2
ENEMY_SHOOT_RANGE = 500
ENEMY_SHOOT_COOLDOWN = 90

moving_left = False
moving_right = False
shoot = False
grenade_key_down = False
grenade_thrown = False

bullet_img = pygame.image.load(os.path.join(BASE_DIR, "img", "icons", "bullet.png")).convert_alpha()
grenade_img = pygame.image.load(os.path.join(BASE_DIR, "img", "icons", "grenade.png")).convert_alpha()

font = pygame.font.SysFont("Futura", 30)

BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
ORANGE = (255, 140, 0)

animation_cache = {}
explosion_frames_cache = None


def draw_bg():
    screen.fill(BG)
    pygame.draw.line(screen, RED, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y))


def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


def draw_health_bar(x, y, health, max_health):
    ratio = max(health, 0) / max_health
    pygame.draw.rect(screen, BLACK, (x - 2, y - 2, 154, 24))
    pygame.draw.rect(screen, RED, (x, y, 150, 20))
    pygame.draw.rect(screen, GREEN, (x, y, 150 * ratio, 20))


def load_soldier_animations(char_type, scale):
    cache_key = (char_type, scale)
    if cache_key in animation_cache:
        return animation_cache[cache_key]

    animation_list = []
    animation_types = ['Idle', 'Run', 'Jump', 'Death']
    for animation in animation_types:
        temp_list = []
        num_of_frames = 5 if animation == 'Idle' else 6

        for i in range(num_of_frames):
            img_path = os.path.join(BASE_DIR, "img", char_type, animation, f"{i}.png")
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(
                    img, (int(img.get_width() * scale), int(img.get_height() * scale))
                )
            else:
                print(f"Missing: {img_path}")
                img = pygame.Surface((int(32 * scale), int(32 * scale)), pygame.SRCALPHA)

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


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, is_ai=False):
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
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        self.animation_list = load_soldier_animations(char_type, scale)
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
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
            self.vel_y = -11
            self.jump = False
            self.in_air = True

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        if self.rect.bottom + dy > GROUND_Y:
            dy = GROUND_Y - self.rect.bottom
            self.in_air = False
            self.vel_y = 0

        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > SCREEN_WIDTH:
            dx = SCREEN_WIDTH - self.rect.right

        self.rect.x += dx
        self.rect.y += dy

    def shoot(self):
        if self.alive and self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(
                self.rect.centerx + (0.6 * self.rect.size[0] * self.direction),
                self.rect.centery,
                self.direction,
                self,
            )
            bullet_group.add(bullet)
            self.ammo -= 1

    def throw_grenade(self):
        if self.alive and self.ammo > 0:
            grenade = Grenade(
                self.rect.centerx + (0.5 * self.rect.size[0] * self.direction),
                self.rect.top,
                self.direction,
                self,
            )
            grenade_group.add(grenade)
            self.ammo -= 1

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]

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
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


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
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
            return

        hits = pygame.sprite.spritecollide(self, characters, False)
        for target in hits:
            if target is self.owner or not target.alive:
                continue
            target.health -= 5
            self.kill()
            break


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

        if self.rect.bottom + dy > GROUND_Y:
            dy = GROUND_Y - self.rect.bottom
            self.vel_y = -self.vel_y * 0.6
            self.speed *= 0.8

        if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
            self.direction *= -1

        self.rect.x += self.direction * self.speed
        self.rect.y += dy

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


def enemy_ai(enemy, player):
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
    else:
        enemy.update_action(0)


bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
characters = pygame.sprite.Group()

player = Soldier('player', 200, 200, 3.0, 5, 20)
characters.add(player)

enemy_list = []
enemy_start_x = 450
for i in range(ENEMY_COUNT):
    enemy = Soldier('enemy', enemy_start_x + i * 150, 200, 3.0, 3, 20, is_ai=True)
    enemy_list.append(enemy)
    characters.add(enemy)

run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a and player.alive:
                moving_left = True
            if event.key == pygame.K_d and player.alive:
                moving_right = True
            if event.key == pygame.K_w and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_q:
                grenade_key_down = True

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

    draw_bg()

    draw_health_bar(10, 10, player.health, player.max_health)
    draw_text(f"AMMO: {player.ammo}", 10, 40)

    enemies_alive = sum(1 for e in enemy_list if e.alive)
    draw_text(f"ENEMIES: {enemies_alive}", SCREEN_WIDTH - 160, 10)

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

        player.move(moving_left, moving_right)
    else:
        draw_text("GAME OVER", SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2, RED)

    for enemy in enemy_list:
        enemy_ai(enemy, player)

    for character in characters:
        character.update()
        character.draw()

    bullet_group.update()
    grenade_group.update()
    explosion_group.update()
    bullet_group.draw(screen)
    grenade_group.draw(screen)
    explosion_group.draw(screen)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()