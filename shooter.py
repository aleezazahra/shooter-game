import pygame 

pygame.init()

SCREEN_WIDTH=800
SCREEN_HEIGHT=int(SCREEN_WIDTH*0.8)

screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("Shooter game")

x=200
y=200
img=pygame.image.load('img/player/Idle/0.png')


rect=img.get_rect()  #used for contolling positions and stuff
rect.center=(x,y)

run=True
while run:

    screen.blit(img,rect)

    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            run=False

    pygame.display.update()

pygame.quit()


