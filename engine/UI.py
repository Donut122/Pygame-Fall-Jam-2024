from engine import asset_manager as assets
import pygame
game = None

class Text:
    def __init__(self, rect: pygame.Rect, text: str, font: str = "calibri", colour: tuple = (255, 255, 255), background_colour: tuple = None, alpha: int = 255, align: str = None, center: bool = False):
        self.rect = pygame.FRect(rect)
        self.pos = self.rect.topleft
        self.text = text
        self.font = font
        self.colour = colour
        self.bg_colour = background_colour
        self.align = align
        self.alpha = alpha
        self.center = center

        self.rect.width = game.renderer.get_text_dimensions(self.text, self.font, self.rect.height, (0, 0), False).width
        if center:
            self.rect.centerx = self.pos[0]

    def render(self, renderer, bounding_box: pygame.Rect):
        self.rect.width = renderer.get_text_dimensions(self.text, self.font, self.rect.height, (0, 0), False).width

        if self.align == "left": self.rect.x = bounding_box.x
        elif self.align == "right": self.rect.right = bounding_box.right
        elif self.align == "top": self.rect.y = bounding_box.y
        elif self.align == "bottom": self.rect.bottom = bounding_box.bottom
        elif self.align == "bottomleft": self.rect.bottomleft = bounding_box.bottomleft
        elif self.align == "bottomright": self.rect.bottomright = bounding_box.bottomright
        elif self.align == "topleft": self.rect.topleft = bounding_box.topleft
        elif self.align == "topright": self.rect.topright = bounding_box.topright
        elif self.align == "center": self.rect.center = bounding_box.center
        else:
            if self.center:
                self.rect.midtop = (self.pos[0] + bounding_box.x, self.pos[1] + bounding_box.y)
            else:
                self.rect.topleft = (self.pos[0] + bounding_box.x, self.pos[1] + bounding_box.y)

        renderer.draw_text(self.text, self.rect.topleft, self.font, self.rect.height / renderer.game.camera.scale, self.colour, self.bg_colour, alpha=self.alpha)

class TextInput:
    def __init__(self, rect: pygame.Rect, default_text: str = "...", font: str = "calibri", colour: tuple = (255, 255, 255), background_colour: tuple = None, max_characters: int = 0, alpha: int = 255, align: str = None, center: bool = False):
        self.rect = pygame.FRect(rect)
        self.pos = self.rect.topleft
        self.text = default_text
        self.default_text = default_text
        self.font = font
        self.colour = colour
        self.bg_colour = background_colour
        self.align = align
        self.alpha = alpha
        self.center = center
        self.typable = True
        self.max_chars = max_characters

    def render(self, renderer, bounding_box: pygame.Rect):
        self.rect.width = renderer.get_text_dimensions(self.text, self.font, self.rect.height, (0, 0), False).width

        if self.align == "left": self.rect.x = bounding_box.x
        elif self.align == "right": self.rect.right = bounding_box.right
        elif self.align == "top": self.rect.y = bounding_box.y
        elif self.align == "bottom": self.rect.bottom = bounding_box.bottom
        elif self.align == "bottomleft": self.rect.bottomleft = bounding_box.bottomleft
        elif self.align == "bottomright": self.rect.bottomright = bounding_box.bottomright
        elif self.align == "topleft": self.rect.topleft = bounding_box.topleft
        elif self.align == "topright": self.rect.topright = bounding_box.topright
        elif self.align == "center": self.rect.center = bounding_box.center
        else:
            if self.center:
                self.rect.center = (self.pos[0] + bounding_box.x, self.pos[1] + bounding_box.y)
            else:
                self.rect.topleft = (self.pos[0] + bounding_box.x, self.pos[1] + bounding_box.y)

        renderer.draw_text(self.text, self.rect.topleft, self.font, self.rect.height / renderer.game.camera.scale, self.colour, self.bg_colour, alpha=self.alpha)

class Frame:
    def __init__(self, rect: pygame.Rect, colour: tuple = None, align: str = None):
        self.rect = pygame.FRect(rect)
        self.pos = rect.topleft
        self.colour = colour
        self.align = align
        self.elements = []

    def render(self, renderer, bounding_box: pygame.Rect):
        if self.align == "left": self.rect.x = bounding_box.x
        elif self.align == "right": self.rect.right = bounding_box.right
        elif self.align == "top": self.rect.y = bounding_box.y
        elif self.align == "bottom": self.rect.bottom = bounding_box.bottom
        elif self.align == "bottomleft": self.rect.bottomleft = bounding_box.bottomleft
        elif self.align == "bottomright": self.rect.bottomright = bounding_box.bottomright
        elif self.align == "topleft": self.rect.topleft = bounding_box.topleft
        elif self.align == "topright": self.rect.topright = bounding_box.topright
        elif self.align == "center": self.rect.center = bounding_box.center
        else: self.rect.topleft = (self.pos[0] + bounding_box.x, self.pos[1] + bounding_box.y)

        if self.colour:
            renderer.renderer.draw_color = self.colour
            renderer.renderer.fill_rect(self.rect)

        for element in self.elements:
            element.render(renderer, self.rect)

    def add(self, element): self.elements.append(element)

    def remove(self, element): self.elements.remove(element)

    def clear(self): self.elements.clear()

class Image:
    def __init__(self, rect: pygame.Rect, texture: str, align: str = None):
        self.rect = pygame.FRect(rect)
        self.pos = rect.topleft
        self.texture = texture
        self.align = align

    def render(self, renderer, bounding_box: pygame.Rect):
        if self.align == "left": self.rect.x = bounding_box.x
        elif self.align == "right": self.rect.right = bounding_box.right
        elif self.align == "top": self.rect.y = bounding_box.y
        elif self.align == "bottom": self.rect.bottom = bounding_box.bottom
        elif self.align == "bottomleft": self.rect.bottomleft = bounding_box.bottomleft
        elif self.align == "bottomright": self.rect.bottomright = bounding_box.bottomright
        elif self.align == "topleft": self.rect.topleft = bounding_box.topleft
        elif self.align == "topright": self.rect.topright = bounding_box.topright
        elif self.align == "center": self.rect.center = bounding_box.center
        else: self.rect.topleft = (self.pos[0] + bounding_box.x, self.pos[1] + bounding_box.y)

        tex, src = assets.get(self.texture)
        tex.draw(src, self.rect)

class Button:
    def __init__(self, rect: pygame.Rect, on_click_callback, texture: str = None, colour: tuple = None, text: str = None, font: str = None, bg_colour: tuple = None, align: str = None):
        self.rect = pygame.FRect(rect)
        self.pos = rect.topleft
        self.texture, self.text, self.font, self.colour, self.bg_colour = texture, text, font, colour, bg_colour
        self.align = align
        self.callback = on_click_callback
    
    def render(self, renderer, bounding_box):
        if self.font != None: self.rect.width = renderer.get_text_dimensions(self.text, self.font, self.rect.height, (0, 0), False).width

        if self.align == "left": self.rect.x = bounding_box.x
        elif self.align == "right": self.rect.right = bounding_box.right
        elif self.align == "top": self.rect.y = bounding_box.y
        elif self.align == "bottom": self.rect.bottom = bounding_box.bottom
        elif self.align == "bottomleft": self.rect.bottomleft = bounding_box.bottomleft
        elif self.align == "bottomright": self.rect.bottomright = bounding_box.bottomright
        elif self.align == "topleft": self.rect.topleft = bounding_box.topleft
        elif self.align == "topright": self.rect.topright = bounding_box.topright
        elif self.align == "center": self.rect.center = bounding_box.center
        else: self.rect.topleft = (self.pos[0] + bounding_box.x, self.pos[1] + bounding_box.y)

        if self.colour and not self.font and not self.texture:
            renderer.renderer.draw_color = self.colour
            renderer.renderer.fill_rect(self.rect)
        
        elif self.colour and self.font and self.text:
            renderer.draw_text(self.text, self.rect.topleft, self.font, self.rect.height / renderer.game.camera.scale, self.colour, self.bg_colour)

        elif self.texture:
            tex, src = assets.get(self.texture)
            tex.draw(src, self.rect)

    def on_click(self):
        self.callback()
