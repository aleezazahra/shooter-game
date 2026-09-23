import pygame

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter game")

clock = pygame.time.Clock()
FPS = 60

# Player action variables
moving_left = False
moving_right = False

# Defining colors
BG = (144, 201, 120)

def draw_bg():
    screen.fill(BG)


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)

        # FIXED: Assign char_type BEFORE loading the image
        self.char_type = char_type
        img = pygame.image.load(f"img/{self.char_type}/Idle/0.png").convert_alpha()
        
        self.speed = speed
        self.direction = 1 # right initial state
        self.flip = False 

        self.image = pygame.transform.scale(
            img, (int(img.get_width() * scale), int(img.get_height() * scale))
        )

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

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


player = Soldier('player', 200, 200, 3.0, 5)
enemy=Soldier('enemy',400,200,3.0,5)
run = True

while run:

    # Handle events
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
    player.move(moving_left, moving_right)
    player.draw()
    enemy.draw()

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()