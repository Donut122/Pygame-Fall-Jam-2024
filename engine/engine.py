import engine.asset_manager as assets
import engine.game_instances as game_instances
import engine.create as create
import pygame
import pygame._sdl2 as sdl2
fixed_res = False
locked_aspect_ratio = None

def update(render: bool = True, physics: bool = True, dt=None, show_stats=False):
    game.update(render, physics, show_stats=show_stats, dt=dt)

def set_fixed_resolution(resolution: tuple):
    global fixed_res
    fixed_res = True
    game.renderer.renderer.logical_size = resolution

def lock_aspect_ratio():
    global locked_aspect_ratio
    locked_aspect_ratio = game.screen.width / game.screen.height

def get_available_drivers() -> list[str]:
    drivers = sdl2.get_drivers()
    driver_names = []

    try:
        while True:
            driver_names.append(drivers.send(None).name)

    except:
        return driver_names

def change_driver(driver_index: int):
    game.change_driver(driver_index)

def get_events(filter_ui: bool = True):
    events = pygame.event.get()
    for event in events.copy():
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                clicked_element = game.UI.on_click(event)
                if clicked_element and filter_ui: events.remove(event)

                if getattr(clicked_element, "typable", False):
                    game.UI.focus = clicked_element
                elif game.UI.focus != None:
                    if not game.UI.focus.text:
                        game.UI.focus.text = game.UI.focus.default_text
                    game.UI.focus = None

        if event.type == pygame.KEYDOWN:
            if game.UI.focus and filter_ui: events.remove(event)

        if event.type == pygame.KEYUP:
            if game.UI.focus:
                if filter_ui: events.remove(event)

                if event.key == pygame.K_RETURN:
                    if not game.UI.focus.text:
                        game.UI.focus.text = game.UI.focus.default_text
                    game.UI.focus = None

                elif event.key == pygame.K_BACKSPACE:
                    if game.UI.focus.text:
                        game.UI.focus.text = game.UI.focus.text[:-1]

                elif event.unicode:
                    if game.UI.focus.max_chars > 0 and len(game.UI.focus.text) < game.UI.focus.max_chars:
                        game.UI.focus.text += event.unicode
                    else:
                        game.UI.focus.text += event.unicode

        if event.type == pygame.WINDOWRESIZED:
            if not fixed_res:
                if locked_aspect_ratio:
                    game.screen.window.size = (game.screen.window.size[1] * locked_aspect_ratio, game.screen.window.size[1])

                game.UI.resize(game.screen.window.size[0] / game.screen.width, game.screen.window.size[1] / game.screen.height)
                game.screen.width, game.screen.height = game.screen.window.size
                game.renderer.resize()
                game.camera.window_resized()
            
            elif locked_aspect_ratio:
                game.screen.window.size = (game.screen.window.size[1] * locked_aspect_ratio, game.screen.window.size[1])
        
    return events

def start(window_resolution: tuple, fullscreen: bool = False, window_title: str = "game", vsync=True, driver=-1):
    global game, camera, scene, physics

    if window_resolution: screen = game_instances.Screen(window_resolution[0], window_resolution[1], fullscreen, window_title)

    game = game_instances.Game(screen if window_resolution else None, vsync=vsync, driver=driver)
    create.game = game

    if window_resolution:
        camera = game.camera

    scene = game.scene
    physics = game.physics
