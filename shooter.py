import os
import pygame

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter Game")

clock = pygame.time.Clock()
FPS = 60

# Player action vars
moving_left = False
moving_right = False

# Defining colors
BG = (144, 201, 120)
RED = (255, 0, 0)

def draw_bg():
    screen.fill(BG)


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        super().__init__()
        self.char_type = char_type
        self.speed = speed
        self.direction = 1  # 1: right, -1: left
        self.flip = False
        
        self.animation_list = []
        self.frame_index = 0
        self.action = 0  # 0: Idle, 1: Run
        self.update_time = pygame.time.get_ticks()

        # Load animation types (0: Idle, 1: Run)
        animation_types = ['Idle', 'Run']
        for animation in animation_types:
            temp_list = []
            num_of_frames = 5 if animation == 'Idle' else 6
            
            for i in range(num_of_frames):
                img_path = f"img/{self.char_type}/{animation}/{i}.png"
                if os.path.exists(img_path):
                    img = pygame.image.load(img_path).convert_alpha()
                    img = pygame.transform.scale(
                        img, (int(img.get_width() * scale), int(img.get_height() * scale))
                    )
                else:
                    img = pygame.Surface((32 * scale, 32 * scale))
                    img.fill(RED if char_type == 'enemy' else (0, 0, 255))
                
                temp_list.append(img)
            
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

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

        self.rect.x += dx
        self.rect.y += dy

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        
        # Check if enuff time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


player = Soldier('player', 200, 200, 3.0, 5)
enemy = Soldier('enemy', 400, 200, 3.0, 5)

run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_ESCAPE:
                run = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False

    draw_bg()
    if moving_left or moving_right:
        player.update_action(1)
    else:
        player.update_action(0)
    player.move(moving_left, moving_right)
    player.update_animation()

    
    player.draw()
    enemy.draw()

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()