import pygame
import os
import json
import glob
import math
from utils.constants import *
from ui.components import Button, draw_panel, draw_text, get_fonts


class MenuScreen:
    def __init__(self, surface):
        self.surface = surface
        self.W, self.H = surface.get_size()

        # State
        self.selected_mode = MODE_HVC
        self.selected_difficulty = None
        self.player1_name = "Player 1"
        self.player2_name = "Computer"
        self.active_input = None
        self.input_texts = {"p1": "Player 1", "p2": "Computer"}
        self.message = ""
        self.saves = []
        self.page = "main"  # main or load

        self._init_buttons()
        self._load_save_list()

    def _init_buttons(self):
        cx = self.W // 2
        
        # Mode buttons
        self.btn_hvh = Button((cx - 220, 265, 200, 50), MODE_HVH,
                              color=C_PANEL2, border_color=C_BORDER)
        self.btn_hvc = Button((cx + 20, 265, 200, 50), MODE_HVC,
                              color=C_PANEL2, border_color=C_BORDER)
                              
        # Difficulty (Shifted up to 365)
        self.btn_easy   = Button((cx - 220, 365, 120, 44), AI_EASY,   color=C_PANEL2, hover_color=(80, 200, 100))
        self.btn_medium = Button((cx - 80,  365, 140, 44), AI_MEDIUM, color=C_PANEL2, hover_color=(240, 250, 50))
        self.btn_hard   = Button((cx + 80,  365, 120, 44), AI_HARD,   color=C_PANEL2, hover_color=(200, 100, 100))
        
        # Actions (Shifted up and gaps slightly tightened)
        self.btn_start  = Button((cx - 120, 510, 240, 46), "  START GAME ",
                                 color=C_ACCENT, hover_color=(100, 150, 255),border_color=C_ACCENT)
        self.btn_load   = Button((cx - 120, 565, 240, 46), "  Load Saved Game",
                                 color=C_PANEL2, border_color=C_BORDER)
        self.btn_exit   = Button((cx - 120, 620, 240, 46), "  Exit Game",
                                 color=C_PANEL2, hover_color=(200, 60, 60), border_color=C_BORDER)

        # Load page
        self.btn_back   = Button((40, 40, 120, 40), "← Back", color=C_PANEL2)
        self.save_buttons = []

    def _load_save_list(self):
        os.makedirs(SAVES_DIR, exist_ok=True)
        self.saves = sorted(glob.glob(os.path.join(SAVES_DIR, "*.json")), reverse=True)

    def _make_save_buttons(self):
        self.save_buttons = []
        for i, path in enumerate(self.saves[:8]):
            name = os.path.splitext(os.path.basename(path))[0]
            btn = Button((self.W // 2 - 220, 130 + i * 60, 440, 48),
                         name, color=C_PANEL2)
            self.save_buttons.append((btn, path))

    def update(self, events):
        fonts = get_fonts()

        if self.page == "load":
            return self._update_load(events)

        # Mode toggle
        if self.btn_hvh.update(events):
            self.selected_mode = MODE_HVH
            self.input_texts["p2"] = "Player 2"
        if self.btn_hvc.update(events):
            self.selected_mode = MODE_HVC
            self.input_texts["p2"] = "Computer"

        # Difficulty
        if self.btn_easy.update(events):   self.selected_difficulty = AI_EASY
        if self.btn_medium.update(events): self.selected_difficulty = AI_MEDIUM
        if self.btn_hard.update(events):   self.selected_difficulty = AI_HARD

        # Input boxes
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                p1_rect = pygame.Rect(self.W // 2 - 220, 455, 190, 40)
                p2_rect = pygame.Rect(self.W // 2 + 30, 455, 190, 40)
                self.active_input = "p1" if p1_rect.collidepoint(mx, my) else \
                                    "p2" if p2_rect.collidepoint(mx, my) else None
            if event.type == pygame.KEYDOWN and self.active_input:
                if event.key == pygame.K_BACKSPACE:
                    self.input_texts[self.active_input] = self.input_texts[self.active_input][:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                    self.active_input = None
                elif len(self.input_texts[self.active_input]) < 14:
                    self.input_texts[self.active_input] += event.unicode

        # Start
        if self.btn_start.update(events):
            return {
                "action": "start_game",
                "mode": self.selected_mode,
                "difficulty": self.selected_difficulty,
                "p1_name": self.input_texts["p1"] or "Player 1",
                "p2_name": self.input_texts["p2"] or ("Computer" if self.selected_mode == MODE_HVC else "Player 2"),
            }

        # Load
        if self.btn_load.update(events):
            self._load_save_list()
            self._make_save_buttons()
            self.page = "load"
            
        # Exit Game
        if self.btn_exit.update(events):
            return {"action": "quit"}

        return None

    def _update_load(self, events):
        if self.btn_back.update(events):
            self.page = "main"
            return None
        for btn, path in self.save_buttons:
            if btn.update(events):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    return {"action": "load_game", "save_data": data}
                except Exception as e:
                    self.message = f"Error loading: {e}"
        return None

    def draw(self):
        self.surface.fill(C_BG)
        self._draw_bg_decoration()
        if self.page == "main":
            self._draw_main()
        else:
            self._draw_load()
        pygame.display.flip()

    def _draw_bg_decoration(self):
        t = pygame.time.get_ticks() / 2000.0
        for i in range(6):
            r = 60 + i * 40
            alpha = 15 + int(8 * math.sin(t + i))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_ACCENT, alpha), (r, r), r, 2)
            self.surface.blit(s, (self.W - r - 60, self.H // 2 - r))

    def _draw_main(self):
        fonts = get_fonts()
        cx = self.W // 2

        # Title
        title = fonts['huge'].render("QUORIDOR", True, C_TEXT_BRIGHT)
        self.surface.blit(title, title.get_rect(centerx=cx, y=80))
        sub = fonts['body'].render("Strategy Board Game  •  AI Opponent", True, C_TEXT_DIM)
        self.surface.blit(sub, sub.get_rect(centerx=cx, y=155))
        # Separator line
        pygame.draw.line(self.surface, C_BORDER, (cx - 180, 175), (cx + 180, 175), 1)

        # Mode label
        draw_text(self.surface, "GAME MODE", (cx, 240), 'small', C_TEXT_DIM, center=True)

        # Mode buttons with active highlight
        for btn, mode in [(self.btn_hvh, MODE_HVH), (self.btn_hvc, MODE_HVC)]:
            is_active = self.selected_mode == mode
            btn.color = C_ACCENT if is_active else C_PANEL2
            btn.border_color = C_ACCENT if is_active else C_BORDER
            btn.draw(self.surface)

        # Difficulty label
        if self.selected_mode == MODE_HVC:
            draw_text(self.surface, "AI DIFFICULTY", (cx, 340), 'small', C_TEXT_DIM, center=True)
            for btn, diff in [(self.btn_easy, AI_EASY), (self.btn_medium, AI_MEDIUM),
                               (self.btn_hard, AI_HARD)]:
                is_active = self.selected_difficulty == diff
                diff_colors = {AI_EASY: (60, 160, 80), AI_MEDIUM: C_GOLD, AI_HARD: (200, 60, 60)}
                btn.color = diff_colors[diff] if is_active else C_PANEL2
                btn.border_color = diff_colors[diff] if is_active else C_BORDER
                btn.draw(self.surface)
        else:
            # Ghost the difficulty buttons
            pass

        # Player name inputs (Labels and rects shifted up)
        draw_text(self.surface, "PLAYER NAMES", (cx, 430), 'small', C_TEXT_DIM, center=True)
        for key, x_off, label in [("p1", -220, "Player 1"), ("p2", 30, "Player 2")]:
            box_rect = pygame.Rect(cx + x_off, 455, 190, 40)
            is_active = self.active_input == key
            col = C_ACCENT if is_active else C_PANEL2
            border = C_ACCENT if is_active else C_BORDER
            pygame.draw.rect(self.surface, col if is_active else C_PANEL2, box_rect, border_radius=6)
            pygame.draw.rect(self.surface, border, box_rect, width=2, border_radius=6)
            text = self.input_texts.get(key, "")
            txt_surf = fonts['body'].render(text + ("|" if is_active else ""), True, C_TEXT_BRIGHT)
            self.surface.blit(txt_surf, (box_rect.x + 10, box_rect.y + 10))

        self.btn_start.draw(self.surface)
        self.btn_load.draw(self.surface)
        self.btn_exit.draw(self.surface)

    def _draw_load(self):
        fonts = get_fonts()
        cx = self.W // 2
        draw_text(self.surface, "Load Saved Game", (cx, 80), 'large', C_TEXT_BRIGHT, center=True)
        self.btn_back.draw(self.surface)
        if not self.save_buttons:
            draw_text(self.surface, "No saved games found.", (cx, 250), 'body', C_TEXT_DIM, center=True)
        for btn, _ in self.save_buttons:
            btn.draw(self.surface)
        if self.message:
            draw_text(self.surface, self.message, (cx, 640), 'body', C_ACCENT2, center=True)