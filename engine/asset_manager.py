import pygame
import pygame._sdl2 as sdl2
import os, math, threading

BASE_DIRECTORY = "assets/"# if not getattr(sys, "frozen", False) else f"{sys._MEIPASS}/assets/"
TEXTURES_DIRECTORY = BASE_DIRECTORY + "textures/"
SOUNDS_DIRECTORY = BASE_DIRECTORY + "sounds/"

textures = {} # name: texture OR (rect, tilemap_name)
surfaces = {} # name: surface
shadows = {} # name: shadow
polygons = {} # name: polygon
sounds = {} # name: sound
fonts = {} # font_name: {"font": font, "tilemap": tilemap, "chars": {{colour: {bg_colour: {char: pygame.Rect}}}}}
threads = {} # name: loading_thread
tilemaps = {} # name: {"texture": texture, "pos": pos}

max_tilemap_size = 7_000

renderer = None # this value is set by the renderer
BLENDMODE_MULT = None
font_resolution = 100
width, height = 0, 0

downscaling = 1

def reset():
    global width, height, renderer, downscaling

    width, height, renderer = 0, 0, None
    downscaling = 1

    textures.clear()
    surfaces.clear()
    shadows.clear()
    fonts.clear()
    threads.clear()

def init(screen):
    global width, height, BLENDMODE_MULT
    width, height = (screen.width, screen.height)

    fonts.clear()

    BLENDMODE_MULT = renderer.compose_custom_blend_mode(
        (6, 1, 1),  # src_color_factor, dst_color_factor, color_operation
        (2, 1, 1)   # src_alpha_factor, dst_alpha_factor, alpha_operation
    )

    make_texture(pygame.Surface((1, 1)), "placeholder")
    surfaces["placeholder"] = pygame.Surface((1, 1))

    for name in tilemaps.keys():
        tilemaps[name]["texture"] = sdl2.Texture.from_surface(renderer, tilemaps[name]["surface"])

def make_tilemap(name: str):
    tilemaps[name] = {"textures": [], "surface": pygame.Surface((1, 1), pygame.SRCALPHA), "pos": (0, 0)}
    tilemaps[name]["texture"] = sdl2.Texture.from_surface(renderer, tilemaps[name]["surface"])

def expand_tilemap(name: str, texture: pygame.Surface):
    global tilemap
    tilemap = tilemaps[name]["surface"]
    pos = tilemaps[name]["pos"]

    if tilemap.width < pos[0] + texture.width:
        new_surf = pygame.Surface((pos[0] + texture.width, tilemap.height), pygame.SRCALPHA)
        new_surf.blit(tilemap)
        tilemaps[name]["surface"] = new_surf
        tilemap = new_surf

    if tilemap.height < pos[1] + texture.height:
        new_surf = pygame.Surface((tilemap.width, pos[1] + texture.height), pygame.SRCALPHA)
        new_surf.blit(tilemap)
        tilemaps[name]["surface"] = new_surf
        tilemap = new_surf

    rect = texture.get_rect(topleft=pos)
    tilemap.blit(texture, rect)
    tilemaps[name]["texture"] = sdl2.Texture.from_surface(renderer, tilemap)
    tilemaps[name]["texture"].blend_mode = pygame.BLENDMODE_BLEND
    tilemaps[name]["textures"].append(rect)

    pos = (rect.right, pos[1])

    if pos[0] > max_tilemap_size:
        pos = (0, rect.bottom)

    tilemaps[name]["pos"] = pos

    return rect

def add_texture_to_tilemap(texture_name: str, tilemap_name: str):
    rect = expand_tilemap(tilemap_name, get(texture_name, True, True)[0])

    textures[texture_name] = (rect, tilemap_name)

def add_textures_to_tilemap(texture_names: list, tilemap_name: str):
    for texture_name in texture_names:
        rect = expand_tilemap(tilemap_name, get(texture_name, True, True)[0])

        textures[texture_name] = (rect, tilemap_name)

def set_dir(directory: str):
    global BASE_DIRECTORY, TEXTURES_DIRECTORY, SOUNDS_DIRECTORY
    BASE_DIRECTORY = directory
    TEXTURES_DIRECTORY = BASE_DIRECTORY + "textures/"
    SOUNDS_DIRECTORY = BASE_DIRECTORY + "sounds/"

def load_texture(file: str, name: str):
    img = pygame.transform.scale_by(pygame.image.load(file), 1 / downscaling)

    textures[name] = sdl2.Texture.from_surface(renderer, img)
    textures[name].blend_mode = pygame.BLENDMODE_BLEND

    surfaces[name] = img

    del threads[name]

def make_texture(surface, name: str):
    texture = sdl2.Texture.from_surface(renderer, surface)
    texture.blend_mode = pygame.BLENDMODE_BLEND
    textures[name] = texture
    surfaces[name] = surface

def get_texture_poly(name: str, precision: int = 0):
    if not name in polygons.keys():
        get(name, True)

        img = surfaces[name]
        size = img.size
        img = pygame.mask.from_surface(img)

        if precision == 0: precision = math.ceil((size[0] if size[0] > size[1] else size[1]) / 25)
        
        outline = img.outline(precision)

        def shift_points(point): return (((point[0] / size[0]) - .5, (point[1] / size[0]) - .5))

        polygons[name] = list(map(shift_points, outline))

    return polygons[name]

def find_file(dir: str):
    for item in os.listdir(dir.replace(dir.split("/")[-1], "")):
        if item.split(".")[0] == dir.split("/")[-1]:
            return dir + "." + item.split(".")[-1]

def make_font(name: str):
    make_tilemap(f"fonts/{name}")
    fonts[name] = {
        "font": pygame.font.SysFont(name, font_resolution),
        "tilemap": f"fonts/{name}",
        "chars": {}
    }

def get_font_texture(name: str) -> sdl2.Texture:
    return tilemaps[fonts[name]["tilemap"]]["texture"]

def get_character(font_name: str, character: str, colour: tuple, bg_colour: tuple) -> pygame.Rect:
    if not font_name in fonts.keys(): make_font(font_name)

    if not colour in fonts[font_name]["chars"].keys():
        fonts[font_name]["chars"][colour] = {}

    if not bg_colour in fonts[font_name]["chars"][colour].keys():
        fonts[font_name]["chars"][colour][bg_colour] = {}

    if not character in fonts[font_name]["chars"][colour][bg_colour].keys():
        make_texture(fonts[font_name]["font"].render(character, True, colour, bg_colour), f"chars/{character}")
        add_texture_to_tilemap(f"chars/{character}", fonts[font_name]["tilemap"])

        fonts[font_name]["chars"][colour][bg_colour][character] = tilemaps[fonts[font_name]["tilemap"]]["textures"][-1]

    return fonts[font_name]["chars"][colour][bg_colour][character]

def get_sound(name, as_path=False) -> pygame.mixer.Sound:
    if not name in textures.keys():
        file = find_file(SOUNDS_DIRECTORY + name)
        if file == None: raise Exception("File Not Found")
        
        if as_path: return file
        else: sounds[name] = pygame.mixer.Sound(file)
    
    return sounds[name]

def get_shadow(name):
    if not name in shadows.keys():
        get(name, True)
        
        img = pygame.transform.scale_by(surfaces[name], 1 / downscaling)
        img = pygame.mask.from_surface(img)
        img = img.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))

        shadows[name] = sdl2.Texture.from_surface(renderer, img)
        shadows[name].blend_mode = pygame.BLENDMODE_BLEND

    return shadows[name]

def get(name, now=False, as_surface=False) -> tuple[sdl2.Texture, pygame.Rect]:
    if name in threads.keys() and now: threads[name].join()
    
    if not name in textures.keys():
        if name in threads.keys():
            return (textures["placeholder"] if not as_surface else surfaces["placeholder"], pygame.Rect(0, 0, 1, 1))

        file = find_file(TEXTURES_DIRECTORY + name)
        if file == None: raise Exception("File Not Found")
        
        thread = threading.Thread(target=load_texture, args=(file, name))
        thread.start()

        threads[name] = thread

        if now: threads[name].join()
        else: return (textures["placeholder"] if not as_surface else surfaces["placeholder"], pygame.Rect(0, 0, 1, 1))
    
    texture = textures[name]

    if as_surface:
        return (surfaces[name], surfaces[name].get_rect())
    else:
        if type(texture) == tuple:
            return (tilemaps[texture[1]]["texture"], texture[0])
        else:
            return (texture, pygame.Rect(0, 0, texture.width, texture.height))
