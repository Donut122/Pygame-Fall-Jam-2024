import pygame, sys
upscaling = 2 # 64x64 * upscaling (64x64 * 2 = 128x128)

class Item():
    def __init__(self, name, image, _class):
        self.name = name 
        self.image = image 
        self._class = _class
        pass

class Inventory:
    def __init__(self):
        self.slots = {'item_1':Item('Dagger', pygame.image.load('assets/textures/Items/dagger.png'), 'weapon'), 'item_2':None,'item_3':None, 'item_4':None}
        self.selected_slot = 1

        self.inventory = pygame.transform.scale_by(pygame.image.load('assets/textures/inventory.png'), upscaling)
        self.slot_size = (15 * upscaling, 14 * upscaling)
        self.inventory_surf = pygame.Surface(self.inventory.size)       
        
    def render(self, surface: pygame.Surface):
        self.inventory_surf.blit(self.inventory)
        self.sells = pygame.Surface(self.slot_size)
        #run now
        if self.slots['item_1'] != None:
            self.inventory_surf.blit(pygame.transform.scale(self.slots['item_1'].image, self.slot_size), (upscaling, 0))
        if self.slots['item_2'] != None:
            self.inventory_surf.blit(pygame.transform.scale(self.slots['item_2'].image, self.slot_size), (self.slot_size[0] + (upscaling * 2), 0))
        if self.slots['item_3'] != None:
            self.inventory_surf.blit(pygame.transform.scale(self.slots['item_3'].image, self.slot_size), ((self.slot_size[0] * 2) + (upscaling * 3), 0))
        if self.slots['item_4'] != None:
            self.inventory_surf.blit(pygame.transform.scale(self.slots['item_4'].image, self.slot_size), ((self.slot_size[0] * 3) + (upscaling * 4), 0))

        surface.blit(self.inventory_surf, self.inventory_surf.get_rect(midbottom = (surface.width / 2, surface.height)))

def resolve_collision(dynamic_rect: pygame.Rect, static_rect: pygame.Rect):
    sides = {
        "left": abs(dynamic_rect.right - static_rect.left),
        "right": abs(dynamic_rect.left - static_rect.right),
        "top": abs(dynamic_rect.bottom - static_rect.top),
        "bottom": abs(dynamic_rect.top - static_rect.bottom)
    }

    closest_side = min(sides.items(), key = lambda side: side[1])[0]

    if closest_side == "left": dynamic_rect.right = static_rect.left
    if closest_side == "right": dynamic_rect.left = static_rect.right
    if closest_side == "top": dynamic_rect.bottom = static_rect.top
    if closest_side == "bottom": dynamic_rect.top = static_rect.bottom

def start():
    window = pygame.display.get_surface()
    clock = pygame.time.Clock()
    dt = .016

    inventory = Inventory()# you a
    player = Player(pygame.transform.scale_by(pygame.image.load("assets/textures/example-player.png"), upscaling))
    camera = Camera((0, 0))
    map = pygame.transform.scale_by(pygame.image.load("assets/textures/map.png"), (upscaling / 1.5))

    test_rect = pygame.Rect(6, 0, 10, 10)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit(0)

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    pause()

        # -- Logic --
        player.update(dt)
        camera.pos = player.rect.center

        if player.rect.colliderect(test_rect):
            resolve_collision(test_rect, player.rect)
            player.x, player.y = (player.rect.centerx / upscaling, player.rect.centery / upscaling)

        # -- Drawing --
        window.fill((0, 0, 0))
        window.blit(map, camera.get_screenspace((-2048 * (upscaling / 1.5), -2048 * (upscaling / 1.5))))
        window.fill((255, 0, 0), (*camera.get_screenspace(test_rect.topleft), 10, 10))
        player.draw(window, camera)
        inventory.render(window)
        pygame.display.flip()

        dt = clock.tick(60) / 1000
        if dt == 0: dt = .016

def pause():
    window = pygame.display.get_surface()
    clock = pygame.time.Clock()

    background = window.copy() # display the last frame of the game behind the menu

    paused = True
    while paused:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit(0)

            elif event.type == pygame.KEUP:
                if event.key == pygame.K_ESCAPE:
                    paused = False

        window.blit(background)

        pygame.display.flip()
        clock.tick(60)

class Camera:
    def __init__(self, pos: tuple[int,int]):
        self.pos = pos
        self.offset = ((32 * upscaling) - pos[0], (32 * upscaling) - pos[1])

    def get_screenspace(self, pos: tuple):
        return (pos[0] + self.offset[0], pos[1] + self.offset[1])

    def __setattr__(self, name, val):
        self.__dict__[name] = val
        if name == "pos":
            self.offset = ((32 * upscaling) - val[0], (32 * upscaling) - val[1])

class Player:
    def __init__(self, player_texture: pygame.Surface):
        # -- Movement --
        self.x, self.y = 0, 0
        self.x_vel, self.y_vel = 0, 0
        self.max_speed = 20
        self.acceleration = 30

        # -- Visuals --
        self.texture = player_texture
        self.rect = player_texture.get_rect()

    def draw(self, surface: pygame.Surface, camera: Camera):
        surface.blit(self.texture, camera.get_screenspace(self.rect.topleft))

    def update(self, dt: float):
        keydown = pygame.key.get_pressed()

        if keydown[pygame.K_w]:
            self.y_vel -= self.acceleration * dt
            if self.y_vel < -self.max_speed:
                self.y_vel = -self.max_speed

        elif keydown[pygame.K_s]:
            self.y_vel += self.acceleration * dt
            if self.y_vel > self.max_speed:
                self.y_vel = self.max_speed

        elif abs(self.y_vel) > 0:
            self.y_vel -= self.acceleration * dt * 2 if self.y_vel > 0 else -self.acceleration * dt * 2
            if abs(self.y_vel) < 1: self.y_vel = 0

        if keydown[pygame.K_a]:
            self.x_vel -= self.acceleration * dt
            if self.x_vel < -self.max_speed:
                self.x_vel = -self.max_speed

        elif keydown[pygame.K_d]:
            self.x_vel += self.acceleration * dt
            if self.x_vel > self.max_speed:
                self.x_vel = self.max_speed

        elif abs(self.x_vel) > 0:
            self.x_vel -= self.acceleration * dt * 2 if self.x_vel > 0 else -self.acceleration * dt * 2
            if abs(self.x_vel) < 1: self.x_vel = 0
        # what do i do next? add enemies? tile collisions?
        
        # ill do collisions, maybe you could add the items to the open world which can be picked up? sure
        # also, add the font that ill send you via discord to the game source ok? :thunbs-up:
        self.x += self.x_vel * dt
        self.y += self.y_vel * dt

        self.rect.center = (self.x * upscaling, self.y * upscaling)