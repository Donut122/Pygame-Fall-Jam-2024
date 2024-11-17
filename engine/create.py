from pymunk import Body, PivotJoint, Shape
import random, math
import pygame
from engine import asset_manager as assets
from engine import UI
game = None

class BaseObject:
    def __init__(self, pos: tuple, size: tuple, center: bool = False, texture: str = None, **kwargs):
        self.initialising = True
        self.x, self.y = pos
        self.pos = pos
        self.width, self.height = size
        self.locked = False

        if center:
            self.x = self.x - (self.width / 2)
            self.y = self.y - (self.height / 2)

        self.texture = texture
        self.rotation = kwargs.get("rotation", 0)
        self.reflection_strength = kwargs.get("reflection_strength", 0)
        self.reflection_direction = kwargs.get("reflection_direction", "top")
        self.dynamic_reflections = kwargs.get("dynamic_reflections", True)
        self.can_reflect = True
        self.opacity = kwargs.get("opacity", 1)

        self.has_shadow = kwargs.get("has_shadow", False)
        self.can_shade = kwargs.get("can_shade", False)

        self.clamps = []

        self.initialising = False

    def lock(self):
        self.locked = True
        self.dstrect = pygame.FRect(
            self.x * game.camera.scale,
            self.y * game.camera.scale,
            self.width * game.camera.scale,
            self.height * game.camera.scale
        )

    def distance_to(self, other_object):
        my_pos = (self.x + (self.width / 2), self.y + (self.height / 2))
        other_pos = (other_object.x + (other_object.width / 2), other_object.y + (other_object.height / 2)) 

        return math.dist(my_pos, other_pos)

    def set_center(self, x: float, y: float):
        self.x = x - (self.width / 2)
        self.y = y - (self.height / 2)

    def unclamp(self, object):
        for i, clamp in enumerate(object.clamps):
            obj, offset = clamp
            if obj == self:
                object.clamps.pop(i)
                return

    def clamp(self, object, offset=(0, 0)):
        object.clamps.append((self, offset))

    def __setattr__(self, name, value):
        self.__dict__[name] = value

        if self.initialising: return

        if name in "xy":
            self.__dict__["pos"] = (self.x, self.y)
            if hasattr(self, "body"):
                self.body.position = (self.x + (self.width / 2), self.y + (self.height / 2))

            for obj, offset in self.clamps:
                obj.x = self.x + offset[0]
                obj.y = self.y + offset[1]

        elif name == "pos":
            self.__dict__["x"] = value[0]
            self.__dict__["y"] = value[1]

            for obj, offset in self.clamps:
                obj.x = self.x + offset[0]
                obj.y = self.y + offset[1]

class TextLabel(BaseObject):
    def __init__(self, pos: tuple, font: str, size: float, colour: tuple, text: str, bg_colour=None, **kwargs):
        super().__init__(pos, (1, 1), **kwargs)

        self.text = text
        self.font = font
        self.font_size = size
        self.font_colour = colour
        self.bg_colour = bg_colour

class Ball(BaseObject):
    def __init__(self, pos: tuple, radius: float, body_type: Body, mass: float = 1, friction: float = 1, elasticity: float = 0.1, texture: str = None, **kwargs):
        super().__init__(pos, (radius * 2, radius * 2), **kwargs)
        self.texture = texture
        self.wrap_to_body = True
        self.physics = game.physics.create_circle(pos, mass, radius, body_type, friction, elasticity)
        self.radius = radius
        self.body = self.physics["body"]
        self.shape = self.physics["shape"]

    def move_constant(self, x: int = 0, y: int = 0):
        self.body.apply_force_at_local_point((x, y))
    
    def move_impulse(self, x: int = 0, y: int = 0):
        self.body.apply_impulse_at_local_point((x, y))

    def rotate_constant(self, vel: int):
        self.body.angular_velocity += vel * game.delta_time

class Box(BaseObject):
    def __init__(self, pos: tuple, size: tuple, body_type: Body, mass: float = 1, friction: float = 1, elasticity: float = 0.1, texture: str = None, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.texture = texture
        self.wrap_to_body = True
        self.physics = game.physics.create_box(pos, size, mass, body_type, friction, elasticity)
        self.body = self.physics["body"]
        self.shape = self.physics["shape"]

    def move_constant(self, x: int = 0, y: int = 0):
        self.body.apply_force_at_local_point((x, y))
    
    def move_impulse(self, x: int = 0, y: int = 0):
        self.body.apply_impulse_at_local_point((x, y))

    def rotate_constant(self, vel: int):
        self.body.angular_velocity += vel * game.delta_time

class Poly(BaseObject):
    def __init__(self, pos: tuple, size: int, body_type: Body, precision: int = 0, mass: float = 1, friction: float = 1, elasticity: float = 0.1, debug=False, texture: str = None, **kwargs):
        super().__init__(pos, (size, size), **kwargs)

        if debug:
            self.texture = f"debug/{texture}"

            surf = pygame.Surface((assets.get(texture)[0].width, assets.get(texture)[0].height), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 0))
            poly = assets.get_texture_poly(texture, precision)

            def remap(pos): return ((pos[0] * (surf.width)) + (surf.width / 2), (pos[1] * (surf.width)) + (surf.width / 2))

            poly = list(map(remap, poly))

            pygame.draw.polygon(surf, (255, 255, 255), poly)

            assets.make_texture(surf, self.texture)

            del surf
        else:
            self.texture = texture

        self.radius = size
        self.wrap_to_body = True
        self.physics = game.physics.create_poly(pos, size, texture, mass, body_type, precision, friction, elasticity)

    def move_constant(self, x: int = 0, y: int = 0):
        self.physics["body"].apply_force_at_local_point((x, y))
    
    def move_impulse(self, x: int = 0, y: int = 0):
        self.physics["body"].apply_impulse_at_local_point((x, y))

    def rotate_constant(self, vel: int):
        self.physics["body"].angular_velocity += vel * game.delta_time

class Water(BaseObject):
    def __init__(self, pos: tuple, size: tuple, density: float = 1.0, texture: str = None, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.texture = texture
        self.wrap_to_body = True
        self.physics = game.physics.create_box(pos, size, 1, Body.STATIC, 0, 0)
        self.shape = self.physics["shape"]
        self.body = self.physics["body"]
        self.is_water = True
        self.density = density

        game.physics.add_water_collision(self.physics, self.on_collision)

    def on_collision(self, shape: Shape, delta: float):
        left, top, right, bottom = shape.bb
        width, height = (right - left, top - bottom)
        density = shape.area / shape.body.mass

        water_width, water_height = (self.shape.bb.right - self.shape.bb.left, self.shape.bb.top - self.shape.bb.bottom)

        left_rel = (left - self.shape.bb.left)
        top_rel = (top - self.shape.bb.bottom)

        right_rel = (right - self.shape.bb.left)
        bottom_rel = (bottom - self.shape.bb.bottom)

        if left_rel < 0: left_rel = 0
        if right_rel < 0: right_rel = 0
        if left_rel > water_width: left_rel = water_width
        if right_rel > water_width: right_rel = water_width

        if bottom_rel < 0: bottom_rel = 0
        if top_rel < 0: top_rel = 0
        if bottom_rel > water_height: bottom_rel = water_height
        if top_rel > water_height: top_rel = water_height

        x_overlap = (right_rel - left_rel) / width
        y_overlap = (bottom_rel - top_rel) / height

        overlap = (x_overlap + y_overlap) / 2

        relative_density = self.density - density
        if relative_density < 0: relative_density = 0

        shape.body.angular_velocity -= delta * shape.body.angular_velocity * overlap * 3

        shape.body.velocity = (
            shape.body.velocity.x - (self.density * delta * shape.body.velocity.x * x_overlap),
            (shape.body.velocity.y + (self.density * delta * shape.body.velocity.y * 3 * y_overlap)) + ((y_overlap * shape.space.gravity[1] * relative_density) * delta)
        )

class Character(BaseObject):
    def __init__(self, pos: tuple, size: tuple, texture: str, mass: float = 3, elasticity=0):
        super().__init__(pos, size)
        self.texture = texture
        self.wrap_to_body = True
        self.physics = game.physics.create_box(pos, size, mass, Body.DYNAMIC, elasticity=elasticity)
        self.body: Body = self.physics["body"]

        self.upright = 0
        self.max_walking_speed = 5
        self.max_falling_speed = 8

    def update(self):
        self.body.angle = math.radians(self.upright)
        self.body.angular_velocity /= 2

        if self.body.velocity[0] < -self.max_walking_speed: self.body.velocity = (-self.max_walking_speed, self.body.velocity[1])
        elif self.body.velocity[0] > self.max_walking_speed: self.body.velocity = (self.max_walking_speed, self.body.velocity[1])

        if self.body.velocity[1] < -self.max_walking_speed: self.body.velocity = (self.body.velocity[0], -self.max_walking_speed)
        elif self.body.velocity[1] > self.max_falling_speed: self.body.velocity = (self.body.velocity[0], self.max_falling_speed)

    def move_constant(self, x: int = 0, y: int = 0):
        self.body.apply_force_at_local_point((x, y))
    
    def move_impulse(self, x: int = 0, y: int = 0):
        self.body.apply_impulse_at_local_point((x, y))

class Hitbox(BaseObject):
    def __init__(self, pos: tuple, size: tuple, friction: float = 1, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.physics = game.physics.create_box(pos, size, 0.1, Body.STATIC, friction)

class ForceField(BaseObject):
    def __init__(self, pos: tuple, size: tuple, force: tuple, limit: tuple = (-1, -1), texture: str = None, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.texture = texture
        self.wrap_to_body = True
        self.physics = game.physics.create_box(pos, size, 1, Body.STATIC, 0, 0)
        self.shape = self.physics["shape"]
        self.body = self.physics["body"]
        self.is_water = True
        self.force = force
        self.limit = limit

        game.physics.add_water_collision(self.physics, self.on_collision)

    def on_collision(self, shape: Shape, delta: float):
        shape.body.velocity = (
            shape.body.velocity[0] + (self.force[0] * delta),
            shape.body.velocity[1] + (self.force[1] * delta)
        )

        if self.limit[0] >= 0:
            if shape.body.velocity[0] < -self.limit[0]:
                shape.body.velocity = (-self.limit[0], shape.body.velocity[1])
            if shape.body.velocity[0] > self.limit[0]:
                shape.body.velocity = (self.limit[0], shape.body.velocity[1])

        if self.limit[1] >= 0:
            if shape.body.velocity[1] < -self.limit[1]:
                shape.body.velocity = (shape.body.velocity[0], -self.limit[1])
            if shape.body.velocity[1] > self.limit[1]:
                shape.body.velocity = (shape.body.velocity[0], self.limit[1])

class Particle:
    def __init__(self, texture: str, duration: float, dimensions: tuple, size: float, end_size: float = None, angle: float = 0, angle_end: float = None, spread: float = 0, spread_end: float = None, volumetric=False, min_distance: float = 1, max_distance: float = None, opacity: float = 1, end_opacity: float = 1, spin_speed: float = 0, time_fun = lambda time: time, flipbook: bool = False):
        self.texture = texture
        self.duration = duration
        self.start_size = size
        self.end_size = size if end_size == None else end_size
        self.angle = angle
        self.angle_end = angle if angle_end == None else angle_end
        self.spread = spread
        self.spread_end = spread if spread_end == None else spread_end
        self.min_distance = min_distance
        self.max_distance = min_distance if max_distance == None else max_distance
        self.opacity = opacity
        self.end_opacity = self.opacity if end_opacity == None else end_opacity
        self.spin_speed = spin_speed
        self.time_fun = time_fun
        self.flipbook = flipbook
        self.dimensions = dimensions
        self.volumetric = volumetric
        factor = dimensions[0]
        self.aspect_ratio = (1, dimensions[1] / factor)

        # actual properties:
        # size, angle, distance, opacity

    def create_particle(self, pos, time):
        rng_spread = .5 - random.random()
        
        part = {
            "birth": time,
            "angle": math.radians(self.angle + (rng_spread * self.spread)),
            "angle end": math.radians(self.angle + (rng_spread * self.spread_end)),
            "distance": self.min_distance + (random.randint(self.min_distance * 100, self.max_distance * 100) / 100),
            "offset": None if not self.volumetric else (random.random(), random.random()),
            "origin": pos
        }
        
        return part

class ParticleEmitter:
    def __init__(self, pos: tuple, particle_properties: Particle, spawnrate: float = 10, active: bool = True):
        self.particles = []
        self.properties = particle_properties
        self.spawnrate = spawnrate
        self.active = active
        self.last_spawn = 0
        self.emitter = True
        self.texture = None
        self.width, self.height = self.properties.aspect_ratio
        self.width *= self.properties.max_distance * 2
        self.height *= self.properties.max_distance * 2
        self.x, self.y = (pos[0] - (self.width / 2), pos[1] - (self.height / 2))
        self.parent = None

    def set_parent(self, object):
        if object == None:
            self.unclamp(object)
            self.parent = None
            return

        self.clamp(object, (-self.width / 2, -self.height / 2))
        self.parent = object

        self.x = self.parent.x - self.width / 2
        self.y = self.parent.y - self.height / 2

    def update(self, dt: float, allowance: int, time: float):
        if not self.active: return

        to_remove = []
        max_spawnrate = allowance / self.properties.duration
        self.last_spawn += dt

        if max_spawnrate > 0:
            if self.spawnrate < max_spawnrate: spawnrate = self.spawnrate
            else: spawnrate = max_spawnrate
        else:
            spawnrate = self.spawnrate

        for particle in self.particles:
            if time - particle["birth"] > self.properties.duration:
                to_remove.append(particle)

        for particle in to_remove:
            self.particles.remove(particle)

        if self.last_spawn > (1 / spawnrate):
            overdraft = self.last_spawn / (1 / spawnrate)
            overdraft = round(overdraft)
            for _ in range(overdraft):
                if len(self.particles) < allowance or allowance == 0:
                    self.last_spawn -= (1 / spawnrate)

                    p = self.properties.create_particle((self.parent.x, self.parent.y) if self.parent else (self.x, self.y), time)
                    if self.properties.volumetric and self.parent != None:
                        p["offset"] = ((p["offset"][0] * self.parent.width) * game.camera.scale, (p["offset"][1] * self.parent.height) * game.camera.scale)

                    self.particles.append(p)
                else:
                    self.last_spawn = 0
                    break

    def unclamp(self, object):
        for i, clamp in enumerate(object.clamps):
            obj, offset = clamp
            if obj == self:
                object.clamps.pop(i)
                return

    def clamp(self, object, offset=(0, 0)):
        object.clamps.append((self, offset))
        self.x, self.y = object.pos
