import pygame
import pygame._sdl2 as sdl2
import engine.asset_manager as asset_manager
from math import degrees as deg
import math, time
pygame.init()

def angle_to(orx: float, ory: float, destx: float, desty: float):
    rot = -(deg(math.atan2(desty - ory, destx - orx)) + 90)

    rot += 360
    rot %= 360

    return rot

def get_screenspace(obj_x: float, obj_y: float, obj_width: float, obj_height: float, cam_off_x: float, cam_off_y: float, cam_scale: float, cam_zoom: float, diagonal_length: float):
    screenspace_size = (obj_width * cam_scale, obj_height * cam_scale)
    screenspace_pos = (((((obj_x + (obj_width / 2)) * cam_scale)) - cam_off_x) - (screenspace_size[0] / 2), ((((obj_y + (obj_height / 2)) * cam_scale)) - cam_off_y) - (screenspace_size[1] / 2))

    screenspace_pos = (
        screenspace_pos[0]+ ((diagonal_length / 4) / cam_zoom),
        screenspace_pos[1] + ((diagonal_length / 4) / cam_zoom)
    )

    return screenspace_pos, screenspace_size

def distance_from_centre(screen, pos: tuple):
    centerx, centery = (screen.width / 2, screen.height / 2)
    return (abs(centerx - pos[0]), abs(centery - pos[1]))

def get_1d_distance(pos1: tuple, pos2: tuple):
    return (abs(pos2[0] - pos1[0]), abs(pos2[1] - pos1[1]))

def genorate_circle(radius, colour, strength):
    mult_map = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    darkness = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    for x in range(radius * 2):
        for y in range(radius * 2):
            col = math.floor(((math.dist((radius, radius), (x, y)) / radius) ** 2) * 255)
            if col > 255: col = 255

            col = 254 - col

            if col < 0: col = 0

            mult_map.fill((col, col, col, col), (x, y, 1, 1))
    
    light = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    light.fill(colour + (strength,))
    light.blit(mult_map, (0, 0), special_flags=pygame.BLEND_MULT)

    darkness.fill((0, 0, 0, 255))
    darkness.blit(mult_map, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    darkness.blit(light, (0, 0))

    return darkness

def onscreen(scr_width: int, scr_height: int, x: int, y: int, width: int, height: int, zoom: float):
    if (x + width) * zoom > -(x + width) and x * zoom < scr_width + width:
        if (y + height) * zoom > -(y + height) and y * zoom < (scr_height + height):
            return True

    return False
    
class Renderer:
    def __init__(self, renderer, screen):
        self.renderer = renderer
        self.game = None
        self.target = None
        self.screen = screen

        self.diagonal_length = math.dist((0, 0), (self.screen.width, self.screen.height))
        self.size = (screen.width, screen.height)
        self.full_size = (screen.width + (self.diagonal_length / 2), screen.height + (self.diagonal_length / 2))
        asset_manager.renderer = renderer
        asset_manager.init(screen)
        self.colour = (255, 255, 255)
        self.shadow_strength = 100
        self.shadow_distance = 3
        self.shadows = True

        self.shaded_objects = [] # [screenspace_rect]
        self.caster_objects = [] # [texture, screenspace_rect]

        self.target = sdl2.Texture(renderer, self.full_size, target=True)

    def resize(self):
        self.diagonal_length = math.dist((0, 0), (self.screen.width, self.screen.height))
        self.size = (self.screen.width, self.screen.height)
        self.full_size = (self.screen.width + (self.diagonal_length / 2), self.screen.height + (self.diagonal_length / 2))

        self.target = sdl2.Texture(self.renderer, self.full_size, target=True)

        asset_manager.init(self.screen)

    def get_text_dimensions(self, text, font, text_size, pos, center) -> pygame.Rect:
        total_width = 0
        current_width = 0
        max_height = 0
        for char in text:
            src = asset_manager.get_character(font, char, (255, 255, 255), (0, 0, 0))

            ratio = src.width / src.height
            src.height = text_size
            src.width = src.height * ratio

            current_width += src.width

            total_width = current_width if current_width > total_width else total_width


            if char == "\n":
                max_height += src.height
                current_width = 0

        if center: x, y = (pos[0] - (total_width / 2), pos[1] - (max_height / 2))
        else: x, y = pos

        return pygame.Rect(x, y, total_width, max_height)

    def draw_text(self, text: str, position: tuple, font: str, text_size: float, text_colour: tuple, text_bg_colour: tuple = None, anti_aa: bool = True, center=False, alpha=255):
        x, y, width, height = self.get_text_dimensions(text, font, text_size * self.game.camera.scale, position, center)


        dstrect = pygame.FRect((x, y), (0, 0))
        for char in text:
            srcrect = asset_manager.get_character(font, char, text_colour, text_bg_colour)
            
            ratio = srcrect.width / srcrect.height
            dstrect.height = text_size * self.game.camera.scale
            dstrect.width = dstrect.height * ratio
            
            img = asset_manager.get_font_texture(font)
            img.alpha = alpha
            img.draw(srcrect, dstrect)
            dstrect.x += dstrect.width

            if char == "\n":
                dstrect.x = x
                dstrect.y += dstrect.height

    def draw_sector(self, game, layer, start_idx, end_idx):
        camera = game.camera

        dstrect = pygame.FRect(0, 0, 1, 1)
        vp = (
            camera.viewport[0] + 2,
            camera.viewport[1] + 2
        )

        objs = game.scene.objects[layer][start_idx:end_idx+1]

        if end_idx >= len(objs): end_idx = len(objs) - 1

        # getting the sectors bounding box
        # checking if the sector is on screen

        lowest_obj = objs[-1]

        if getattr(lowest_obj, "wrap_to_body", False):
            hitbox = lowest_obj.physics["body"]

            lowest_obj.rotation = deg(hitbox.angle)
            lowest_obj.pos = (hitbox.position.x - (lowest_obj.width / 2), hitbox.position.y - (lowest_obj.height / 2))

        low_y = ((lowest_obj.y + lowest_obj.height) - camera.y)

        highest_obj = objs[0]

        if getattr(highest_obj, "wrap_to_body", False):
            hitbox = highest_obj.physics["body"]

            highest_obj.rotation = deg(hitbox.angle)
            highest_obj.pos = (hitbox.position.x - (highest_obj.width / 2), hitbox.position.y - (highest_obj.height / 2))

        high_y = (highest_obj.y - camera.y)

        if high_y > vp[1]:  return
        if low_y < -vp[1]: return


        left_obj = max(objs, key=lambda obj: obj.physics["body"].position.x if hasattr(obj, "physics") else obj.x)

        if getattr(left_obj, "wrap_to_body", False):
            hitbox = left_obj.physics["body"]

            left_obj.rotation = deg(hitbox.angle)
            left_obj.pos = (hitbox.position.x - (left_obj.width / 2), hitbox.position.y - (left_obj.height / 2))

        left_x = ((left_obj.x + left_obj.width) - camera.x)

        right_obj =min(objs, key=lambda obj: obj.physics["body"].position.x if hasattr(obj, "physics") else obj.x)

        if getattr(right_obj, "wrap_to_body", False):
            hitbox = right_obj.physics["body"]

            right_obj.rotation = deg(hitbox.angle)
            right_obj.pos = (hitbox.position.x - (right_obj.width / 2), hitbox.position.y - (right_obj.height / 2))

        right_x = (right_obj.x - camera.x)

        if right_x > vp[0]: return
        if left_x < -vp[0]: return


        for object in objs:
            if getattr(object, "is_model", False): 
                self.draw_model(object, game)
                continue

            if getattr(object, "wrap_to_body", False):
                hitbox = object.physics["body"]

                object.rotation = deg(hitbox.angle)
                object.pos = (hitbox.position.x - (object.width / 2), hitbox.position.y - (object.height / 2))
            
            self.draw_object(object, game, dstrect)

    def draw_object(self, object, game, dstrect):
        camera = game.camera
        
        # calculating the dstrect

        if getattr(object, "locked", False):
            screenspace_pos = (self.origin[0] + object.dstrect.x, self.origin[1] + object.dstrect.y)
            screenspace_size = object.dstrect.size
        else:
            screenspace_pos, screenspace_size = get_screenspace(object.x, object.y, object.width, object.height, camera.offset_x, camera.offset_y, camera.scale, camera.zoom, self.diagonal_length)

        dstrect.x, dstrect.y = screenspace_pos[0], screenspace_pos[1]
        dstrect.width, dstrect.height = screenspace_size[0], screenspace_size[1]

        # calling objects draw function if one is present

        if hasattr(object, "on_draw"): object.on_draw(object)

        if object.texture != None: # drawing the object
            texture, srcrect = asset_manager.get(object.texture)
            transparrency = (getattr(object, "opacity", 1)) * 255
            if transparrency > 255: transparrency = 255
            if transparrency < 0: transparrency = 0
            texture.alpha = transparrency

            texture.draw(srcrect, dstrect, object.rotation)

            if self.shadows:
                if object.has_shadow: self.caster_objects.append((asset_manager.get_shadow(object.texture), dstrect.copy(), object.rotation))
                elif object.can_shade: self.shaded_objects.append(dstrect.copy())

        if getattr(object, "emitter", False): # drawing particles
            particle_rect = pygame.Rect(1, 1, 1, 1)

            if not object.properties.flipbook:
                texture, srcrect = asset_manager.get(object.properties.texture)
            else:
                tilemap = asset_manager.tilemaps[object.properties.texture]
                texture = tilemap["texture"]

            for particle in object.particles:
                progress = (game.time - particle["birth"]) / object.properties.duration
                if progress > 1: progress = 1
                progress = object.properties.time_fun(progress)

                size = object.properties.start_size + ((object.properties.end_size - object.properties.start_size) * progress)
                opacity = object.properties.opacity + ((object.properties.end_opacity - object.properties.opacity) * progress)
                distance = particle["distance"] * progress * camera.scale
                angle = particle["angle"] + ((particle["angle end"] - particle["angle"]) * progress)

                particle_rect.width = object.properties.dimensions[0] * size * camera.scale
                particle_rect.height = object.properties.dimensions[1] * size * camera.scale

                offset = (
                    (particle["origin"][0] - object.x) * camera.scale,
                    (particle["origin"][1] - object.y) * camera.scale
                )

                if object.properties.volumetric:
                    particle_rect.center = (
                        dstrect.x + (distance * math.sin(angle) * .5) + particle["offset"][0] + offset[0],
                        dstrect.y + (distance * math.cos(angle) * .5) + particle["offset"][1] + offset[1]
                    )
                else: particle_rect.center = (dstrect.centerx + (distance * math.sin(angle) * .5) + object.offset[0], dstrect.centery + (distance * math.cos(angle) * .5) + object.offset[1])

                transparrency = opacity * 255
                if transparrency > 255: transparrency = 255
                if transparrency < 0: transparrency = 0
                texture.alpha = transparrency

                if object.properties.flipbook:
                    srcrect = tilemap["textures"][round(progress * (len(tilemap["textures"]) - 1))]

                texture.draw(srcrect, particle_rect, object.properties.spin_speed * (game.time - particle["birth"]))

        if getattr(object, "font", None) != None: # drawing text
            self.draw_text(object.text, dstrect.center, object.font, object.font_size, object.font_colour, getattr(object, "bg_colour", None), center=True)
           
    def draw_game(self, game):
        # Preparation
        self.game = game
        self.renderer.target = self.target
        self.renderer.clear()

        self.screen_rect = pygame.Rect(0, 0, self.full_size[0], self.full_size[1])
        self.window_rect = pygame.Rect(0, 0, self.size[0], self.size[1])
        self.caster_objects.clear()
        self.shaded_objects.clear()

        camera = game.camera
        self.renderer.draw_color = self.colour

        self.origin = get_screenspace(0, 0, 0, 0, camera.offset_x, camera.offset_y, camera.scale, camera.zoom, self.diagonal_length)[0]

        # Drawing background (tiled and untiled)

        if game.background != None:
            if game.background_tiled:
                offset = (
                    game.camera.x * game.camera.scale * .01 % self.full_size[0],
                    game.camera.y * game.camera.scale * .01 % self.full_size[1],
                )

                for x in range(-1, 2):
                    for y in range(-1, 2):
                        asset_manager.get(game.background)[0].draw(dstrect=pygame.Rect(0 - offset[0] + (self.full_size[0] * x), 0 - offset[1] + (self.full_size[1] * y), self.full_size[0], self.full_size[1]))
            else:
                asset_manager.get(game.background)[0].draw(dstrect=pygame.Rect(0, 0, self.full_size[0], self.full_size[1]))

        # Drawing the scene

        self.renderer.scale = (camera.zoom, camera.zoom)
        self.zoom = camera.zoom

        for layer in game.scene.objects.keys():
            game.scene.objects[layer] = sorted(game.scene.objects[layer], key=lambda obj: obj.physics["body"].position.y if hasattr(obj, "physics") else obj.y)

        for layer in sorted(game.scene.objects.keys(), reverse=True):
            objs = game.scene.objects[layer]
            sectors = math.ceil(len(objs) / (10 + (len(objs) / 30)))

            for i in range(sectors):
                i += 1
                self.draw_sector(game, layer, math.floor((len(objs) / sectors) * (i-1)), math.ceil((len(objs) / sectors) * i))

        self.shaded_objects = sorted(self.shaded_objects, key=lambda rect: rect.y)

        for texture, caster, caster_rotation in self.caster_objects:
            caster: pygame.Rect
            start = caster.center
            end = (caster.center[0] + (math.sin(game.shadow_direction) * (self.full_size[1] / camera.zoom)), caster.center[1] + (math.cos(game.shadow_direction) * (self.full_size[1] / camera.zoom)))

            for shader in self.shaded_objects:
                shader: pygame.Rect
                clip = shader.clipline(start, end)

                if clip:
                    y_distance = get_1d_distance(caster.midbottom, clip[0])[1] / self.shadow_distance

                    if y_distance < 1: y_distance = 1

                    old_w = caster.width
                    caster.width -= y_distance
                    caster.height -= y_distance

                    if caster.width <= 0: break

                    shrinkage = caster.width / old_w

                    caster.centerx = clip[0][0]
                    caster.y = clip[0][1]

                    texture.alpha = round(self.shadow_strength * shrinkage)

                    texture.draw(dstrect=caster, angle=caster_rotation)

                    break

        # Rotating the scene

        self.renderer.scale = (1, 1)
        self.renderer.target = None
        dstrect = pygame.Rect(0, 0, self.target.width, self.target.height)
        dstrect.center = self.window_rect.center
        self.target.draw(dstrect=dstrect, angle=camera.rotation)

        # UI

        for element in game.UI.elements:
            element.render(self, self.window_rect)

        for text in game.text_to_draw:
            self.draw_text(*text)
        game.text_to_draw.clear()

        self.renderer.present()
