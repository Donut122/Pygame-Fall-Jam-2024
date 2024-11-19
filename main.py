import pygame
import sys
import game

width, height = 128, 128
window = pygame.display.set_mode((width, height), pygame.SCALED)
clock = pygame.time.Clock()

def on_start_button_click():
    game.start()

main_menu = pygame.transform.scale_by(pygame.image.load("assets/textures/main menu.png"), 2)
start_button = pygame.Rect(0, 0, width, height)
# button is the size of the screen for now

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit(0)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if start_button.collidepoint(event.pos):
                    on_start_button_click()
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE: sys.exit(0)

    window.blit(main_menu)

    pygame.display.flip()
    clock.tick(60)