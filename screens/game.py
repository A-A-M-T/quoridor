import pygame
import os
import json
import math
import time
import threading
from datetime import datetime

from game_state import GameState
from game.ai import QuoridorAI
from ui.components import Button, draw_panel, draw_text, get_fonts
from ui.board_renderer import (draw_board, pixel_to_cell,
                                pixel_to_h_wall, pixel_to_v_wall)
from utils.constants import *


SIDEBAR_X = BOARD_OFFSET_X + BOARD_SIZE * CELL_SIZE + (BOARD_SIZE - 1) * WALL_THICKNESS + 30
SIDEBAR_W = 260


class GameScreen:
    def __init__(self, surface, config):
        self.surface = surface
        self.W, self.H = surface.get_size()
        self.config = config
        self.mode = config.get("mode", MODE_HVC)
        self.difficulty = config.get("difficulty", AI_MEDIUM)
        self.p_names = {
            1: config.get("p1_name", "Player 1"),
            2: config.get("p2_name", "AI" if self.mode == MODE_HVC else "Player 2"),
        }

        self.state = GameState()
        self.valid_moves = []
        self.wall_mode = False
        self.wall_orientation = 'h'
        self.wall_hover = None
        self.wall_invalid = False
        self.hover_cell = None
        self.message = ""
        self.message_timer = 0
        self.ai_thinking = False
        self.ai_thread = None
        self.ai_move_result = None

        self.ai = None
        if self.mode == MODE_HVC:
            self.ai = QuoridorAI(2, self.difficulty)

        # Load save if provided
        if config.get("action") == "load_game" and "save_data" in config:
            self._load_from_dict(config["save_data"])

        self._init_buttons()
        self._refresh_valid_moves()

    def _init_buttons(self):
        sx = SIDEBAR_X
        sw = SIDEBAR_W
        bw = (sw - 10) // 2

        # Control mode toggle
        self.btn_wall_mode = Button((sx, 340, sw, 44), "Wall Mode [W]",
                                    color=C_PANEL2, border_color=C_BORDER)
        self.btn_rotate = Button((sx, 392, sw, 38), "Rotate Wall [R]",
                                 color=C_PANEL2, border_color=C_BORDER, font_key='small')

        # Undo
        self.btn_undo = Button((sx, 445, sw, 40), "<- Undo",
                               color=C_PANEL2, border_color=C_BORDER)

        # Save / Reset
        self.btn_save  = Button((sx, 498, bw, 40), "Save",
                                color=C_PANEL2, border_color=C_BORDER)
        self.btn_reset = Button((sx + bw + 10, 498, bw, 40), "Reset",
                                color=(80, 35, 35), border_color=(150, 60, 60))

        # Exit
        self.btn_exit  = Button((sx, 552, sw, 44), "X   Exit to Menu",
                                color=(55, 30, 30), border_color=(150, 60, 60),
                                hover_color=(100, 40, 40))

    def _refresh_valid_moves(self):
        self.valid_moves = self.state.get_valid_pawn_moves() if not self.state.winner else []

    def _set_message(self, msg, duration=2.5):
        self.message = msg
        self.message_timer = time.time() + duration

    def update(self, events):
        if time.time() > self.message_timer:
            self.message = ""

        # AI move handling
        if self.ai_thinking:
            if self.ai_move_result is not None:
                self._apply_ai_move(self.ai_move_result)
                self.ai_move_result = None
                self.ai_thinking = False
                self._refresh_valid_moves()
            return None

        # Trigger AI if it's AI's turn
        if (self.mode == MODE_HVC and self.state.current_player == 2 and not self.state.winner and not self.ai_thinking):
            self.ai_thinking = True
            self.ai_move_result = None
            
            # --- FIX HERE: Pass a completely isolated snapshot copy of the state to the thread ---
            if hasattr(self.state, 'copy'):
                state_snapshot = self.state.copy()
            elif hasattr(self.state, 'to_dict'): # Fallback if you have serialization built-in
                state_snapshot = GameState()
                state_snapshot.from_dict(self.state.to_dict())
            else:
                state_snapshot = copy.deepcopy(self.state)
                
            t = threading.Thread(target=self._ai_thread_func, args=(state_snapshot,), daemon=True)
            t.start()

        # Mouse position
        mx, my = pygame.mouse.get_pos()
        self.hover_cell = pixel_to_cell(mx, my)

        # Wall hover detection
        if self.wall_mode:
            if self.wall_orientation == 'h':
                wh = pixel_to_h_wall(mx, my)
                self.wall_hover = ('h', wh[0], wh[1]) if wh else None
            else:
                wh = pixel_to_v_wall(mx, my)
                self.wall_hover = ('v', wh[0], wh[1]) if wh else None

            if self.wall_hover:
                ori, wr, wc = self.wall_hover
                self.wall_invalid = not self.state.is_valid_wall(ori, wr, wc)
            else:
                self.wall_invalid = False
        else:
            self.wall_hover = None

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    self.wall_mode = not self.wall_mode
                    self._set_message("Wall mode " + ("ON" if self.wall_mode else "OFF"), 1.2)
                elif event.key == pygame.K_r:
                    self.wall_orientation = 'v' if self.wall_orientation == 'h' else 'h'
                    self._set_message(f"Wall: {'Horizontal' if self.wall_orientation == 'h' else 'Vertical'}", 1.2)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.state.winner:
                    # Only allow human to interact on their turn
                    if not (self.mode == MODE_HVC and self.state.current_player == 2):
                        self._handle_board_click(mx, my)

        # Sidebar buttons
        if self.btn_wall_mode.update(events):
            self.wall_mode = not self.wall_mode
            self._set_message("Wall mode " + ("ON" if self.wall_mode else "OFF"), 1.2)

        if self.btn_rotate.update(events):
            self.wall_orientation = 'v' if self.wall_orientation == 'h' else 'h'

        if self.btn_undo.update(events):
            # Undo twice in HvC mode (AI + player move)
            if self.mode == MODE_HVC:
                self.state.undo()
            if self.state.undo():
                self._refresh_valid_moves()
                self._set_message("Move undone.", 1.5)

        if self.btn_save.update(events):
            self._save_game()

        if self.btn_reset.update(events):
            self.state.reset()
            self.wall_mode = False
            self._refresh_valid_moves()
            self._set_message("Game reset!", 2)

        if self.btn_exit.update(events):
            return {"action": "menu"}

        return None

    def _handle_board_click(self, mx, my):
        if self.wall_mode:
            if self.wall_hover and not self.wall_invalid:
                ori, wr, wc = self.wall_hover
                if self.state.place_wall(ori, wr, wc):
                    self.wall_mode = False
                    self._refresh_valid_moves()
                    self._check_winner()
                else:
                    self._set_message("Invalid wall placement!", 2)
        else:
            cell = pixel_to_cell(mx, my)
            if cell and cell in self.valid_moves:
                self.state.move_pawn(*cell)
                self._refresh_valid_moves()
                self._check_winner()
            elif cell:
                self._set_message("Invalid move!", 1.5)

    def _check_winner(self):
        if self.state.winner:
            name = self.p_names[self.state.winner]
            self._set_message(f"WINNER: {name}!", 999)

    def _ai_thread_func(self, state_snapshot):
        move = self.ai.get_move(state_snapshot)
        self.ai_move_result = move

    def _apply_ai_move(self, move):
        if move is None:
            return
        if move['type'] == 'pawn':
            self.state.move_pawn(*move['pos'])
        else:
            self.state.place_wall(move['orientation'], move['row'], move['col'])
        self._check_winner()

    def _save_game(self):
        os.makedirs(SAVES_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVES_DIR, f"save_{ts}.json")
        data = {
            "state": self.state.to_dict(),
            "mode": self.mode,
            "difficulty": self.difficulty,
            "p1_name": self.p_names[1],
            "p2_name": self.p_names[2],
            "saved_at": ts,
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        self._set_message(f"Saved: save_{ts}.json", 3)

    def _load_from_dict(self, data):
        self.state.from_dict(data["state"])
        self.mode = data.get("mode", self.mode)
        self.difficulty = data.get("difficulty", self.difficulty)
        self.p_names[1] = data.get("p1_name", "Player 1")
        self.p_names[2] = data.get("p2_name", "Player 2")
        if self.mode == MODE_HVC:
            self.ai = QuoridorAI(2, self.difficulty)
        self._refresh_valid_moves()

    def draw(self):
        self.surface.fill(C_BG)

        # Draw board
        draw_board(
            self.surface, self.state,
            valid_moves=self.valid_moves,
            hover_cell=self.hover_cell,
            wall_hover=self.wall_hover,
            wall_mode=self.wall_mode,
            wall_invalid=self.wall_invalid,
        )

        # Draw sidebar
        self._draw_sidebar()

        # Winner overlay
        if self.state.winner:
            self._draw_winner_overlay()

    def _draw_sidebar(self):
        fonts = get_fonts()
        sx = SIDEBAR_X
        sw = SIDEBAR_W

        # Panel background
        draw_panel(self.surface, (sx - 12, 10, sw + 24, self.H - 20),
                   color=C_PANEL, border_color=C_BORDER, border_radius=12)

        # Title
        draw_text(self.surface, "QUORIDOR", (sx + sw // 2, 30),
                  'heading', C_TEXT_BRIGHT, center=True)
        pygame.draw.line(self.surface, C_BORDER, (sx, 60), (sx + sw, 60))

        # Player info panels
        for player in [1, 2]:
            y_base = 75 + (player - 1) * 110
            is_turn = self.state.current_player == player and not self.state.winner
            ai_tag = " (AI)" if (self.mode == MODE_HVC and player == 2) else ""
            color = C_P1 if player == 1 else C_P2

            # Panel
            bg = C_PANEL2 if is_turn else C_PANEL
            draw_panel(self.surface, (sx, y_base, sw, 100),
                       color=bg, border_color=color if is_turn else C_BORDER,
                       border_radius=8)

            # Pawn dot
            pygame.draw.circle(self.surface, color, (sx + 20, y_base + 24), 12)
            lbl = fonts['bold'].render(str(player), True, C_TEXT_BRIGHT)
            self.surface.blit(lbl, lbl.get_rect(center=(sx + 20, y_base + 24)))

            # Name
            name = self.p_names[player] + ai_tag
            draw_text(self.surface, name, (sx + 40, y_base + 14), 'bold', C_TEXT_BRIGHT)

            # Turn badge
            if is_turn:
                if self.ai_thinking and player == 2:
                    badge = "Thinking..."
                else:
                    badge = "YOUR TURN"
                badge_surf = fonts['small'].render(badge, True, color)
                self.surface.blit(badge_surf, (sx + 40, y_base + 38))

            # Walls remaining
            walls = self.state.walls_left[player]
            draw_text(self.surface, "Walls:", (sx + 12, y_base + 62), 'small', C_TEXT_DIM)
            # Wall pips
            for i in range(WALLS_PER_PLAYER):
                wx = sx + 65 + i * 16
                wy = y_base + 68
                pip_color = color if i < walls else C_PANEL
                pygame.draw.rect(self.surface, pip_color, (wx, wy, 10, 16), border_radius=2)
                pygame.draw.rect(self.surface, C_BORDER, (wx, wy, 10, 16), width=1, border_radius=2)

        pygame.draw.line(self.surface, C_BORDER, (sx, 300), (sx + sw, 300))

        # Wall mode indicator
        y_wm = 310
        draw_text(self.surface, "INPUT MODE", (sx + sw // 2, y_wm),
                  'small', C_TEXT_DIM, center=True)
        mode_txt = ("Wall" if self.wall_mode else "Pawn")
        ori_txt = f"  [{('H' if self.wall_orientation == 'h' else 'V')}]" if self.wall_mode else ""
        draw_text(self.surface, mode_txt + ori_txt,
                  (sx + sw // 2, y_wm + 20), 'bold',
                  C_GOLD if self.wall_mode else C_ACCENT, center=True)

        # Buttons
        self.btn_wall_mode.color = C_GOLD if self.wall_mode else C_PANEL2
        self.btn_wall_mode.border_color = C_GOLD if self.wall_mode else C_BORDER
        self.btn_wall_mode.draw(self.surface)
        self.btn_rotate.draw(self.surface)
        self.btn_undo.draw(self.surface)
        self.btn_save.draw(self.surface)
        self.btn_reset.draw(self.surface)
        self.btn_exit.draw(self.surface)

        # Controls hint
        draw_text(self.surface, "W = wall mode  •  R = rotate",
                  (sx + sw // 2, 605), 'small', C_TEXT_DIM, center=True)

        # Message
        if self.message:
            clean_msg = self.message.replace("🏆 ", "") # Safe fallback cleanup
            color = C_GOLD if "wins" in clean_msg.lower() else \
                    C_ACCENT2 if "Invalid" in clean_msg else C_TEXT_BRIGHT
            msg_surf = fonts['body'].render(clean_msg, True, color)
            self.surface.blit(msg_surf, msg_surf.get_rect(
                centerx=sx + sw // 2, y=645))

    def _draw_winner_overlay(self):
        fonts = get_fonts()
        winner = self.state.winner
        name = self.p_names[winner]
        color = C_P1 if winner == 1 else C_P2

        # Semi-transparent overlay over board area
        ov_w = BOARD_SIZE * CELL_SIZE + (BOARD_SIZE - 1) * WALL_THICKNESS + 16
        ov_h = 120
        ov_x = BOARD_OFFSET_X - 8
        ov_y = BOARD_OFFSET_Y + (BOARD_SIZE * CELL_SIZE + (BOARD_SIZE - 1) * WALL_THICKNESS) // 2 - 60

        s = pygame.Surface((ov_w, ov_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 190))
        self.surface.blit(s, (ov_x, ov_y))
        pygame.draw.rect(self.surface, color, (ov_x, ov_y, ov_w, ov_h),
                         width=3, border_radius=10)
        
        txt = fonts['large'].render(f"{name} Wins!", True, color)
        sx2 = int(txt.get_width())
        sy2 = int(txt.get_height())
        scaled = pygame.transform.smoothscale(txt, (sx2, sy2))
        self.surface.blit(scaled, scaled.get_rect(
            center=(ov_x + ov_w // 2, ov_y + ov_h // 2)))