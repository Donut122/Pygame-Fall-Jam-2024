import pygame
import pygame._sdl2 as sdl2
import engine.renderer as renderer
import pymunk
import math
import time
import engine.asset_manager as assets
import engine.UI as UI

class PhysicsScene:
    def __init__(self, gravity: float = 10):
        self.is_stepping = False
        self.space = pymunk.Space()
        self.space.gravity = (0, gravity)
        self.callbacks = {} # object: function
        self.handler = self.space.add_default_collision_handler()
        self.handler.begin = self.on_collision
        self.handler.separate = self.on_separate
        self.to_add = []
        self.to_remove = []
        self.floating_objects = []
        self.count = 0
        self.quality = 3

        self.water_callbacks = {}

    def set_gravity(self, strength: float):
        self.space.gravity = (0, strength)

    def step_catchup(self):
        for obj in self.to_add:
            try:
                self.add(obj, real=True)
            except: ...

        for obj in self.to_remove:
            try:
                self.remove_object(obj, real=True)
            except: ...
        
        self.to_add.clear()
        self.to_remove.clear()

    def remove_water_collision(self, object):
        del self.water_callbacks[object["body"]]

    def add_water_collision(self, object, function):
        self.water_callbacks[object["body"]] = function

    def add_collision_callback(self, object, function):
        self.callbacks[object["body"]] = function

    def remove_collision_callback(self, object):
        del self.callbacks[object["body"]]

    def on_separate(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict):
        try:
            for i, shape in enumerate(arbiter.shapes):
                other = arbiter.shapes[1] if i == 0 else arbiter.shapes[0]

                if shape.body in list(self.water_callbacks.keys()):
                    self.floating_objects.remove((shape.body, other))
                    return False

            return True
        except: return True

    def on_collision(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict):
        try:
            for i, shape in enumerate(arbiter.shapes):
                other = arbiter.shapes[1] if i == 0 else arbiter.shapes[0]
                if shape.body in list(self.callbacks.keys()):
                    self.callbacks[shape.body](other.body)

                if shape.body in list(self.water_callbacks.keys()):
                    self.floating_objects.append((shape.body, other))
                    return False

            return True
        except: return True

    def remove_object(self, object, real=False):
        if not real:
            self.to_remove.append(object)
        else:
            obj = object

            if object in list(self.callbacks.keys()):
                del self.callbacks[obj["body"]]

            try:
                if "constraints" in obj.keys():
                    for constraint in obj["constraints"]:
                        self.space.remove(constraint)
            
            except: pass

            try:
                self.space.remove(obj["body"], obj["shape"])
                self.count -= 1
            except: pass

    def remove_constraints_from_object(self, object):
        obj = object.physics
        if "constraints" not in obj.keys(): return

        for constraint in obj["constraints"]:
            self.space.remove(constraint)
        
        del obj["constraints"]

    def connect(self, object1, object2, connect_at: tuple = None):
        if type(object1) == pymunk.Body:
            body1 = object1
        else:
            body1 = object1.physics["body"]

        if type(object2) == pymunk.Body:
            body2 = object2
        else:
            body2 = object2.physics["body"]

        middle = ((body1.position.x + body2.position.x) / 2, (body1.position.y + body2.position.y) / 2)

        constraint = pymunk.PivotJoint(body1, body2, middle if connect_at == None else connect_at)

        if not "constraints" in object1.physics.keys():
            object1.physics["constraints"] = []

        object1.physics["constraints"].append(constraint)

        self.space.add(constraint)

    def add(self, physics: dict, real=False):
        if not real: self.to_add.append(physics)
        else:
            self.space.add(physics["body"], physics["shape"])
            self.count += 1

    def create_circle(self, pos: tuple, mass: int, radius: int, body_type, friction: float = 1, elasticity: float = 0.1, func=None) -> int:
        body = pymunk.Body(mass, 0, body_type=body_type)
        shape = pymunk.Circle(body, radius)

        body.position = pos
        shape.friction = friction
        shape.elasticity = elasticity
        shape.mass = mass

        return {"body": body, "shape": shape, "shape type": "circle"}
    
    def create_box(self, pos: tuple, size: tuple, mass: int, body_type, friction: float = 1, elasticity: float = 0.1, func=None) -> int:
        body = pymunk.Body(mass, 0, body_type)
        shape = pymunk.Poly.create_box(body, size)
        body.position = (pos[0] + (size[0] / 2), pos[1] + (size[1] / 2))

        shape.friction = friction
        shape.elasticity = elasticity
        shape.mass = mass

        return {"body": body, "shape": shape, "shape type": "box"}

    def create_poly(self, pos: tuple, size: int, texture: str, mass: int, body_type, precision: int = 0, friction: float = 1, elasticity: float = 0.1, func=None) -> int:
        body = pymunk.Body(mass, 0, body_type)

        texture_poly = assets.get_texture_poly(texture, precision)
        transform = pymunk.Transform.scaling(size)
        shape = pymunk.Poly(body, texture_poly, transform=transform)

        body.position = (pos[0] + (size / 2), pos[1] + (size / 2))
        shape.friction = friction
        shape.elasticity = elasticity
        shape.mass = mass

        return {"body": body, "shape": shape, "shape type": "poly"}

    def update(self, delta: float):
        for water_body, other_shape in self.floating_objects:
            self.water_callbacks[water_body](other_shape, delta)

        self.is_stepping = True

        step = delta / self.quality

        for _ in range(self.quality):
            self.space.step(step)

        self.is_stepping = False
        self.step_catchup()

class Screen:
    def __init__(self, width: int, height: int, fullscreen: bool, title: str = "pygame window", resizable=True, position: tuple = None, driver: str = "automatic"):
        monitor_info = pygame.display.Info()
        monitor_size = (monitor_info.current_w, monitor_info.current_h)

        if fullscreen: self.width, self.height = monitor_size
        else: self.width, self.height = width, height

        self.size = (self.width, self.height)
        self.pos = (0, 0)
        self.fullscreen = fullscreen

        self.window = pygame.Window(title, (width, height), position if position != None else pygame.WINDOWPOS_UNDEFINED, fullscreen_desktop=fullscreen, opengl="opengl" in driver)
        self.window.resizable = resizable

    def reopen(self, driver: str = "automatic"):
        new_window = pygame.Window(self.window.title, self.window.size, self.window.position, fullscreen_desktop=self.fullscreen, opengl="opengl" in driver)
        new_window.resizable = self.window.resizable

        self.window.destroy()
        self.window = new_window

class Scene:
    def __init__(self, game):
        self.objects = {}
        self.textures = {}
        self.emitters = []
        self.remove_queue = []
        self.add_queue = []
        self.game = game
        self.count = 0

    def object_layer(self, object):
        for layer in self.objects.keys():
            if object in self.objects[layer]:
                return layer
        
        return None

    def clear(self, layer: int = None):
        if layer == None:
            for layer in list(self.objects.keys()):
                for object in list(self.objects[layer]):
                    self.remove(object)

                del self.objects[layer]

        else:
            if layer not in self.objects.keys(): return
            
            for object in self.objects[layer].copy():
                self.remove(object)

            del self.objects[layer]

    def add(self, object, layer: int = 1):
        self.count += 1
        if not layer in self.objects.keys():
            self.objects[layer] = []

        self.objects[layer].append(object)

        if hasattr(object, "physics"):
            self.game.physics.add(object.physics)

        if hasattr(object, "emitter"):
            self.emitters.append(object)

    def remove(self, object):
        for layer in self.objects.keys():
            if object in self.objects[layer]:
                self.objects[layer].remove(object)
                self.count -= 1
                break
                
        if getattr(object, "physics", None) != None:
            self.game.physics.remove_object(object.physics)

        if hasattr(object, "emitter"):
            self.emitters.remove(object)

    def update_particles(self, dt: float):
        if not len(self.emitters): return
        allowance = self.get_particle_allowance()

        for emitter in self.emitters:
            emitter.update(dt, allowance, self.game.time)

    def get_particle_allowance(self):
        return self.game.particle_cap // len(self.emitters)

    def get_particle_count(self):
        particles = 0

        for emitter in self.emitters:
            particles += len(emitter.particles)

        return particles

    def set_background_color(self, colour: tuple):
        self.game.renderer.colour = colour

class Camera:
    def __init__(self, x: float, y: float, screen, game):
        self.screen = screen
        self.game = game
        self.x, self.y = x, y
        self.zoom = 1
        self.rotation = 0
        self.scale = screen.height / 10
        self.offset_x, self.offset_y = ((x * self.scale) - (screen.width / 2), (y * self.scale) - (screen.height / 2))
        self.viewport = ((self.screen.width / self.scale) / self.zoom, 10.0 / self.zoom)
        self.subject = None

    def window_resized(self):
        self.scale = self.screen.height / 10
        self.update()

    def set_pos(self, x: float, y: float, floor=False):
        if floor:
            x = math.floor(x * 1000) / 1000
            y = math.floor(y * 1000) / 1000

        self.x, self.y = x, y

    def update(self):
        if self.subject != None:
            self.x = self.subject.x + (self.subject.width / 2)
            self.y = self.subject.y + (self.subject.height / 2)

        self.offset_x = (self.x * self.scale) - ((self.screen.width / 2) / self.zoom)
        self.offset_y = (self.y * self.scale) - ((self.screen.height / 2) / self.zoom)

        self.viewport = ((self.screen.width / self.scale) / self.zoom, 10.0 / self.zoom)

    def get_mouse_target(self, mouse_pos: tuple, filter=list()):
        x, y = self.screenspace_to_worldspace(mouse_pos)

        for layer in self.game.scene.objects.keys():
            for obj in self.game.scene.objects[layer]:
                if obj in filter: continue
                if x > obj.x and x < obj.x + obj.width:
                    if y > obj.y and y < obj.y + obj.height:
                        return obj

    def screenspace_to_worldspace(self, screenspace_pos: tuple) -> tuple[int,int]:
        pos = (
            (((screenspace_pos[0] - (self.screen.width / 2)) / self.scale) / self.zoom) + self.x,
            (((-(-screenspace_pos[1] + (self.screen.height / 2))) / self.scale) / self.zoom) + self.y
        )

        return pos

class SoundSystem:
    def __init__(self, game):
        self.game = game
        self.scene = game.scene
        self.camera = game.camera

        self.playlist = []
        self.playlist_pos = 0

    def update(self):
        if self.playlist and not pygame.mixer.music.get_busy():
            self.on_song_finish()

    def restart_playlist(self):
        self.playlist_pos = 0
        pygame.mixer.music.unload()
        self.start_playlist()

    def get_current_song(self):
        if self.playlist:
            return self.playlist[self.playlist_pos]
        else:
            return None

    def on_song_finish(self):
        print("ended")
        self.playlist_pos += 1
        if self.playlist_pos >= len(self.playlist):
            self.playlist_pos = 0
            print("restarting")

        if self.playlist:
            pygame.mixer.music.load(self.get_current_song())
            pygame.mixer.music.play()

    def set_music_volume(self, volume: float): pygame.mixer.music.set_volume(volume)

    def pause_music(self): pygame.mixer.music.pause()

    def start_playlist(self):
        self.playlist_pos = 0
        pygame.mixer.music.load(self.get_current_song())
        pygame.mixer.music.play()
    
    def resume_music(self): pygame.mixer.music.unpause()

    def restart_song(self): pygame.mixer.music.rewind()

    def add_song(self, song: str):
        self.playlist.append(assets.get_sound(song, as_path=True))

    def remove_song(self, song: str):
        if song in self.playlist:
            self.playlist.remove(song)
    
    def play_sound(self, sound: str, volume: float = 1, loops: int = 0, playtime: float = 0, fade_ms: float = 0, pos: tuple = None, falloff_distance: float = 3):
        snd = assets.get_sound(sound)
        snd.set_volume(volume)

        if pos == None:
            snd.play(loops, playtime, fade_ms)

        else:
            relative_pos = (
                self.camera.x - pos[0],
                self.camera.y - pos[1]
            )
            distance = math.dist((self.camera.x, self.camera.y), pos)

            if distance > falloff_distance:
                distance = 1 + (distance - falloff_distance)
                snd.set_volume(volume / distance)

            channel = pygame.mixer.find_channel()
            channel.set_volume(1 if relative_pos[0] < falloff_distance else 1 - distance, 1 if relative_pos[0] > -falloff_distance else 1 - distance)
            channel.play(snd, loops, playtime, fade_ms)

    def play_sound_at_object(self, sound: str, object, volume: float = 1, loops: int = 0, playtime: float = 0, fade_ms: float = 0, falloff_distance: float = 3):
        self.play_sound(sound, volume, loops, playtime, fade_ms, (object.x + (object.width / 2), object.y + (object.height / 2)), falloff_distance)

class GUI:
    def __init__(self):
        self.elements = []
        self.focus = None

    def resize(self, growth_x: float, growth_y: float):
        def size_element(element):
            element.rect.width *= growth_x
            element.rect.height *= growth_y
            element.pos = (
                element.pos[0] * growth_x,
                element.pos[1] * growth_y
            )

            if hasattr(element, "elements"):
                for item in element.elements:
                    size_element(item)

        for element in self.elements:
            size_element(element)

    def is_touching_pos(self, pos: tuple):
        def check_element(element):
            if element.rect.collidepoint(pos):
                if hasattr(element, "elements"):
                    for i in range(len(element.elements)):
                        ret = check_element(element.elements[len(element.elements) - (i + 1)])
                        if ret: return True
                
                return True

        for i in range(len(self.elements)):
            ret = check_element(self.elements[len(self.elements) - (i + 1)])
            if ret: return True

        return False

    def on_click(self, event):
        def check_element(element):
            if element.rect.collidepoint(event.pos):
                if hasattr(element, "elements"):
                    for item in element.elements:
                        ret = check_element(item)
                        if ret: return ret

                if hasattr(element, "on_click"):
                    element.on_click()
                
                return element

        for element in self.elements:
            ret = check_element(element)
            if ret: return ret

        return None

    def add(self, element): self.elements.append(element)

    def remove(self, element): self.elements.remove(element)

    def clear(self): self.elements.clear()

class Game:
    def __init__(self, screen, vsync=True, driver=-1):
        self.screen = screen
        self.time = 0

        if screen:
            self.UI = GUI()
            UI.game = self
            self.camera = Camera(0, 0, screen, self)
            self.renderer = renderer.Renderer(sdl2.Renderer(screen.window, index=driver, vsync=vsync), screen)

        self.scene = Scene(self)
        self.physics = PhysicsScene()
        self.sound = SoundSystem(self)
        self.clock = pygame.time.Clock()
        self.max_fps = 60
        self.text_to_draw = []
        self.new_delta_time = 0.016
        self.delta_time = 0.016
        self.last_delta_time = 0.016
        self.oldest_delta_time = 0.016
        self.max_delta_time = 1 / 24
        self.running = True
        self.shadow_direction = 0
        self.particle_cap = 0
        self.vsync = vsync
        self.driver_name = "automatic"

        self.render_time = 0
        self.physics_time = 0

        self.background = None

    def set_background(self, texture: str, tiled: bool = False):
        self.background = texture
        self.background_tiled = tiled

    def get_drivers(self):
        drivers = sdl2.get_drivers()
        driver_names = []

        try:
            while True:
                driver_names.append(drivers.send(None).name)

        except:
            return driver_names

    def change_driver(self, driver_index: int):
        del self.renderer
        assets.reset()
        self.driver_name = "automatic" if driver_index == -1 else self.get_drivers()[driver_index]
        self.screen.reopen(self.driver_name)
        self.renderer = renderer.Renderer(sdl2.Renderer(self.screen.window, index=driver_index, vsync=self.vsync), self.screen)

    def quit(self):
        self.running = False
        self.screen.window.destroy()
        
    def draw_text(self, text: str, pos: tuple, font: str, text_size: int, text_colour: tuple, text_bg_colour: tuple = None, anti_aa: bool = True, centred=False):
        self.text_to_draw.append((text, pos, font, text_size, text_colour, text_bg_colour, anti_aa, centred))

    def render_stats(self):
        stats = [
            f"fps: {round(1/self.new_delta_time)}",
            f"draw: {self.render_time * 1000:.2f}ms",
            f"physics: {self.physics_time * 1000:.2f}ms",
            f"objects: {self.scene.count:,}",
            f"physics objects: {self.physics.count:,}",
            f"particles: {self.scene.get_particle_count()} / {self.particle_cap if self.particle_cap else 'inf'}",
            f"driver: {self.driver_name}"
        ]

        y = 0
        for stat in stats:
            self.draw_text(stat, (0, y), "comic sans", 1, (0, 0, 0), (255, 255, 255))
            y += self.camera.scale

    def update(self, render=True, update_simulation=True, show_stats=False, dt=None):
        self.start_time = time.perf_counter()
        self.camera.update()
        self.sound.update()
        
        if render and show_stats:
            s = time.perf_counter()
            self.renderer.draw_game(self)
            e = time.perf_counter()

            self.render_time = e-s
        elif render:
            self.renderer.draw_game(self)
        
        self.oldest_delta_time = self.last_delta_time
        self.last_delta_time = self.new_delta_time
        self.clock.tick(self.max_fps)

        if update_simulation and show_stats:
            s = time.perf_counter()
            self.physics.update(self.delta_time if dt == None else dt)
            self.scene.update_particles(self.delta_time if dt == None else dt)
            self.time += self.delta_time if dt == None else dt
            e = time.perf_counter()

            self.physics_time = e-s

        elif update_simulation:
            self.physics.update(self.delta_time if dt == None else dt)
            self.scene.update_particles(self.delta_time if dt == None else dt)
            self.time += self.delta_time if dt == None else dt

        elif show_stats: self.physics_time = 0
        
        if show_stats:
            self.render_stats()

        self.new_delta_time = time.perf_counter() - self.start_time

        self.delta_time = (self.oldest_delta_time + self.last_delta_time + self.new_delta_time) / 3

        if self.delta_time > self.max_delta_time: self.delta_time = self.max_delta_time
