"""
UI Helper Components: Button, Panel, fonts
"""

import pygame
from utils.constants import (
    C_ACCENT, C_ACCENT2, C_PANEL, C_PANEL2, C_BORDER,
    C_TEXT, C_TEXT_DIM, C_TEXT_BRIGHT, C_BG, C_GOLD
)


def load_fonts():
    fonts = {}
    try:
        fonts['title']  = pygame.font.SysFont("Georgia", 52, bold=True)
        fonts['heading'] = pygame.font.SysFont("Georgia", 28, bold=True)
        fonts['body']   = pygame.font.SysFont("Segoe UI", 20)
        fonts['small']  = pygame.font.SysFont("Segoe UI", 16)
        fonts['bold']   = pygame.font.SysFont("Segoe UI", 20, bold=True)
        fonts['large']  = pygame.font.SysFont("Georgia", 36, bold=True)
        fonts['huge']   = pygame.font.SysFont("Georgia", 64, bold=True)
    except Exception:
        default = pygame.font.Font(None, 32)
        fonts = {k: default for k in ['title','heading','body','small','bold','large','huge']}
    return fonts


FONTS = None

def get_fonts():
    global FONTS
    if FONTS is None:
        FONTS = load_fonts()
    return FONTS


class Button:
    def __init__(self, rect, text, color=None, text_color=None,
                 border_color=None, font_key='bold', hover_color=None,
                 border_radius=8):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color or C_PANEL2
        self.hover_color = hover_color or tuple(min(c + 25, 255) for c in self.color)
        self.text_color = text_color or C_TEXT_BRIGHT
        self.border_color = border_color or C_BORDER
        self.font_key = font_key
        self.border_radius = border_radius
        self.hovered = False
        self.disabled = False

    def update(self, events):
        mx, my = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mx, my) and not self.disabled
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.hovered:
                    return True
        return False

    def draw(self, surface):
        fonts = get_fonts()
        color = self.hover_color if self.hovered else self.color
        if self.disabled:
            color = tuple(c // 2 for c in self.color)
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.border_color, self.rect,
                         width=2, border_radius=self.border_radius)
        font = fonts.get(self.font_key, fonts['bold'])
        tc = self.text_color if not self.disabled else C_TEXT_DIM
        txt = font.render(self.text, True, tc)
        surface.blit(txt, txt.get_rect(center=self.rect.center))


def draw_panel(surface, rect, color=None, border_color=None, border_radius=12, alpha=None):
    color = color or C_PANEL
    border_color = border_color or C_BORDER
    r = pygame.Rect(rect)
    if alpha:
        s = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        s.fill((*color, alpha))
        surface.blit(s, r.topleft)
    else:
        pygame.draw.rect(surface, color, r, border_radius=border_radius)
    pygame.draw.rect(surface, border_color, r, width=1, border_radius=border_radius)


def draw_text(surface, text, pos, font_key='body', color=None,
              center=False, fonts=None):
    if fonts is None:
        fonts = get_fonts()
    color = color or C_TEXT
    font = fonts.get(font_key, fonts['body'])
    surf = font.render(str(text), True, color)
    if center:
        surface.blit(surf, surf.get_rect(center=pos))
    else:
        surface.blit(surf, pos)
    return surf.get_rect(topleft=pos)
