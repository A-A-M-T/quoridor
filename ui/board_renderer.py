"""
Board Renderer
Draws the Quoridor board: cells, wall slots, walls, pawns, highlights
"""

import pygame
import math
from utils.constants import *


def cell_rect(r, c):
    """Return the pygame.Rect for the cell at (row, col)."""
    x = BOARD_OFFSET_X + c * (CELL_SIZE + WALL_THICKNESS)
    y = BOARD_OFFSET_Y + r * (CELL_SIZE + WALL_THICKNESS)
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def h_wall_rect(r, c):
    """Rect for horizontal wall slot below row r, between col c and c+1.
       Wall covers TWO cells wide."""
    x = BOARD_OFFSET_X + c * (CELL_SIZE + WALL_THICKNESS)
    y = BOARD_OFFSET_Y + r * (CELL_SIZE + WALL_THICKNESS) + CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE * 2 + WALL_THICKNESS, WALL_THICKNESS)


def v_wall_rect(r, c):
    """Rect for vertical wall slot right of col c, between row r and r+1."""
    x = BOARD_OFFSET_X + c * (CELL_SIZE + WALL_THICKNESS) + CELL_SIZE
    y = BOARD_OFFSET_Y + r * (CELL_SIZE + WALL_THICKNESS)
    return pygame.Rect(x, y, WALL_THICKNESS, CELL_SIZE * 2 + WALL_THICKNESS)


def pixel_to_cell(px, py):
    """Convert pixel position to (row, col) or None."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if cell_rect(r, c).collidepoint(px, py):
                return r, c
    return None


def pixel_to_h_wall(px, py):
    """Return (r, c) of horizontal wall slot under cursor, or None."""
    for r in range(BOARD_SIZE - 1):
        for c in range(BOARD_SIZE - 1):
            if h_wall_rect(r, c).collidepoint(px, py):
                return r, c
    return None


def pixel_to_v_wall(px, py):
    """Return (r, c) of vertical wall slot under cursor, or None."""
    for r in range(BOARD_SIZE - 1):
        for c in range(BOARD_SIZE - 1):
            if v_wall_rect(r, c).collidepoint(px, py):
                return r, c
    return None


def draw_board(surface, state, valid_moves=None, hover_cell=None,
               wall_hover=None, wall_mode=False, wall_invalid=False,
               player_names=None):
    """Main board drawing function."""
    valid_moves = valid_moves or []

    # Background board area
    board_pixel_w = BOARD_SIZE * CELL_SIZE + (BOARD_SIZE - 1) * WALL_THICKNESS
    board_pixel_h = board_pixel_w
    board_rect = pygame.Rect(
        BOARD_OFFSET_X - 8, BOARD_OFFSET_Y - 8,
        board_pixel_w + 16, board_pixel_h + 16
    )
    pygame.draw.rect(surface, C_PANEL, board_rect, border_radius=6)
    pygame.draw.rect(surface, C_BORDER, board_rect, width=2, border_radius=6)

    # Draw goal rows (subtle highlight)
    for c in range(BOARD_SIZE):
        r1 = cell_rect(0, c)
        r2 = cell_rect(BOARD_SIZE - 1, c)
        s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        s.fill((*C_P2, 30))
        surface.blit(s, r1.topleft)
        s2 = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        s2.fill((*C_P1, 30))
        surface.blit(s2, r2.topleft)

    # Cells
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            rect = cell_rect(r, c)
            if (r, c) in valid_moves and not wall_mode:
                color = C_CELL_VALID_H if (r, c) == hover_cell else C_CELL_VALID
            elif (r, c) == hover_cell and not wall_mode:
                color = C_CELL_HOVER
            else:
                color = C_CELL
            pygame.draw.rect(surface, color, rect, border_radius=3)

            # Coordinate labels (optional, subtle)
            if r == BOARD_SIZE - 1:
                from ui.components import get_fonts
                f = get_fonts()['small']
                t = f.render(str(c + 1), True, C_TEXT_DIM)
                surface.blit(t, (rect.centerx - t.get_width() // 2,
                                 rect.bottom + 4))
            if c == 0:
                from ui.components import get_fonts
                f = get_fonts()['small']
                t = f.render(chr(ord('A') + r), True, C_TEXT_DIM)
                surface.blit(t, (rect.left - 20, rect.centery - t.get_height() // 2))

    # Existing walls
    for (wr, wc) in state.h_walls:
        rect = h_wall_rect(wr, wc)
        # Determine color by which player placed it (we track via color heuristic)
        pygame.draw.rect(surface, C_WALL_P1, rect, border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255, 40), rect, width=1, border_radius=3)

    for (wr, wc) in state.v_walls:
        rect = v_wall_rect(wr, wc)
        pygame.draw.rect(surface, C_WALL_P2, rect, border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255, 40), rect, width=1, border_radius=3)

    # Wall hover preview
    if wall_mode and wall_hover:
        ori, wr, wc = wall_hover
        if ori == 'h':
            rect = h_wall_rect(wr, wc)
        else:
            rect = v_wall_rect(wr, wc)
        color = C_WALL_INVALID if wall_invalid else C_WALL_PREVIEW
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((*color, 160))
        surface.blit(s, rect.topleft)
        pygame.draw.rect(surface, color, rect, width=2, border_radius=3)

    # Pawns
    _draw_pawn(surface, state, 1)
    _draw_pawn(surface, state, 2)


def _draw_pawn(surface, state, player):
    r, c = state.positions[player]
    rect = cell_rect(r, c)
    cx, cy = rect.center
    color = C_P1 if player == 1 else C_P2
    dark = C_P1_DARK if player == 1 else C_P2_DARK

    # Shadow
    pygame.draw.circle(surface, (0, 0, 0), (cx + 3, cy + 4), PAWN_RADIUS)
    # Main circle
    pygame.draw.circle(surface, dark, (cx, cy), PAWN_RADIUS)
    pygame.draw.circle(surface, color, (cx, cy), PAWN_RADIUS - 3)
    # Highlight
    pygame.draw.circle(surface, tuple(min(c + 60, 255) for c in color),
                       (cx - 6, cy - 6), 8)
    # Number label
    from ui.components import get_fonts
    fonts = get_fonts()
    lbl = fonts['bold'].render(str(player), True, (255, 255, 255))
    surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

    # Pulse ring when it's this player's turn
    if state.current_player == player and not state.winner:
        t = pygame.time.get_ticks() / 600.0
        alpha = int(80 + 70 * math.sin(t))
        pulse_r = PAWN_RADIUS + 6
        pulse_surf = pygame.Surface((pulse_r * 2 + 4, pulse_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(pulse_surf, (*color, alpha),
                           (pulse_r + 2, pulse_r + 2), pulse_r, 3)
        surface.blit(pulse_surf, (cx - pulse_r - 2, cy - pulse_r - 2))
