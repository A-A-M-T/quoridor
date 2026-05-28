"""
Game Constants and Configuration
"""

# Window
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 750
FPS = 60
TITLE = "Quoridor - CSE472s AI Project"

# Board
BOARD_SIZE = 9
CELL_SIZE = 60
WALL_THICKNESS = 10
WALL_LENGTH = CELL_SIZE * 2 + WALL_THICKNESS
BOARD_OFFSET_X = 80
BOARD_OFFSET_Y = 60

# Total board pixel size
BOARD_PIXEL = BOARD_SIZE * CELL_SIZE + (BOARD_SIZE - 1) * WALL_THICKNESS

# Colors - Dark elegant theme
C_BG           = (15, 17, 26)
C_BG2          = (22, 26, 40)
C_PANEL        = (28, 33, 52)
C_PANEL2       = (35, 41, 65)
C_BORDER       = (55, 65, 100)
C_ACCENT       = (82, 130, 255)
C_ACCENT2      = (255, 100, 80)
C_GOLD         = (220, 175, 60)
C_TEXT         = (220, 225, 245)
C_TEXT_DIM     = (130, 140, 170)
C_TEXT_BRIGHT  = (255, 255, 255)

# Board colors
C_CELL         = (30, 36, 58)
C_CELL_HOVER   = (45, 55, 90)
C_CELL_VALID   = (40, 90, 60)
C_CELL_VALID_H = (55, 120, 80)
C_WALL_SLOT    = (22, 26, 40)
C_WALL_SLOT_H  = (60, 75, 110)
C_WALL_P1      = (15, 15, 15)
C_WALL_P2      = (15, 15, 15)
C_WALL_PREVIEW = (150, 180, 255)
C_WALL_INVALID = (180, 60, 60)

# Player colors
C_P1           = (82, 130, 255)
C_P2           = (255, 100, 80)
C_P1_DARK      = (50, 90, 180)
C_P2_DARK      = (180, 60, 50)

# Pawn
PAWN_RADIUS = 22

# Walls per player
WALLS_PER_PLAYER = 10

# Game modes
MODE_HVH = "Human vs Human"
MODE_HVC = "Human vs Computer"

# AI Difficulty
AI_EASY   = "Easy"
AI_MEDIUM = "Medium"
AI_HARD   = "Hard"

# Saves directory
SAVES_DIR = "saves"
