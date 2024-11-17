import pygame
from engine import engine, create
import sys

width, height = 500, 500
engine.start((width, height), vsync=False)
engine.game.renderer.colour = (10, 10, 10)

def on_start_button_click(): ...

main_menu = create.UI.Frame(pygame.Rect(0, 0, width, height), (0, 0, 0))
engine.game.UI.add(main_menu)

title = create.UI.Text(pygame.Rect(width / 2, 0, 1, height / 8), "Game Title Here plz", center=True)
start_button = create.UI.Button(
    pygame.Rect(0, 0, width / 4, height / 8),
    on_start_button_click,
    colour=(0, 0, 0),
    bg_colour=(25, 240, 25),
    text="Start",
    font="calibri",
    align="center"
)
logo = create.UI.Image(pygame.Rect(0, 0, width / 4, height / 8), "title screen/pygame-ce logo", "bottomright")

main_menu.add(title)
main_menu.add(start_button)
main_menu.add(logo)

engine.lock_aspect_ratio()

while True:
    for event in engine.get_events():
        if event.type == pygame.QUIT: sys.exit(0)
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE: sys.exit(0)

    engine.update()
