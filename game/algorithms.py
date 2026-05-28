from collections import deque
import copy
import math
import random

# Global memory to prevent Horizon Effect oscillation (Paranoia)
_AI_HISTORY = {1: None, 2: None}

# Returns the shortest path distance from the player's pawn - to the goal row.
# Smaller distance = closer to winning.
def get_shortest_path_distance(state, player):  
    return state.shortest_path_length(player)

# Creates a NEW copied game state and applies a move to it.
# This is important because the original state should not change
# while Minimax is testing moves.
def apply_move(state, move):
    # Deep copy creates a full independent copy of the board state
    new_state = copy.deepcopy(state)
    
    # If the move is a pawn movement
    if move['type'] == 'pawn':
        # Move the pawn to the new position
        new_state.move_pawn(*move['pos'])
    else:
        # Place the wall using:  -- orientation -> 'h' or 'v' -- row, col -> wall position
        new_state.place_wall(move['orientation'], move['row'], move['col'])
    return new_state


# ==========================================================
# Evaluation 
# ==========================================================
# Evaluates how good the current board state is for the given player.
# Positive score -> good for player
# Negative score -> good for opponent
def evaluate_state(state, player, ai_type):
    opponent = 2 if player == 1 else 1 # Determine opponent player number
    my_dist = get_shortest_path_distance(state, player) # Distance from current player to victory
    opp_dist = get_shortest_path_distance(state, opponent) # Distance from opponent to victory
    
    if (ai_type == "hard"):
        # Moving forward is worth 20 points per step. Delaying the opponent is worth 30 points.
        score = (opp_dist * 30) - (my_dist * 20)
        
        # Walls are extremely precious (Costs 50 points to use).
        score += (state.walls_left[player] * 50)
        score -= (state.walls_left[opponent] * 20)

        # Huge positive score if player already won
        if state.winner == player: return 100000
        # Huge negative score if opponent already won
        if state.winner == opponent: return -100000
        return score
    else:
        # For medium AI, we use a simpler evaluation that focuses more on distance and less on walls.
        
        # Base score:
        # If opponent distance is bigger and my distance is smaller, the score becomes higher (better for us)
        score = (opp_dist - my_dist) * 20
        
        # Bonus for having more remaining walls
        # Walls are valuable because they can block opponent
        score += (state.walls_left[player] - state.walls_left[opponent]) * 3

        if state.winner == player: return 100000
        if state.winner == opponent: return -100000
        return score


def generate_moves(state, player, allow_walls=True):
    moves = []
    
    # GENERATE PAWN MOVES
    # Get all valid pawn movements for the player
    for move in state.get_valid_pawn_moves(player):
        moves.append({
            'type': 'pawn',
            'pos': move
        })
        
    # GENERATE WALL MOVES
    # Only generate wall moves if:
    # - allow_walls is True
    # - player still has walls remaining
    if allow_walls and state.walls_left[player] > 0:
        opponent = 2 if player == 1 else 1  # Determine opponent player number
        orow, ocol = state.positions[opponent]

        candidates = []         # Store possible wall candidates
        
        # Search around opponent position to place blocking walls nearby
        # max/min prevent index out of bounds
        for r in range(max(0, orow - 2), min(8, orow + 2)):
            for c in range(max(0, ocol - 2), min(8, ocol + 2)):
                candidates.append(('h', r, c))
                candidates.append(('v', r, c))
                
        # CHECK VALID WALLS
        # Test every candidate wall
        for ori, r, c in candidates:
            if state.is_valid_wall(ori, r, c):       # Check if wall placement is legal
                moves.append({                       # Add wall move to moves list
                    'type': 'wall',
                    'orientation': ori,
                    'row': r,
                    'col': c
                })

    return moves

# ======================== AI DECISION MAKING ========================

# Orders moves to help the AI search smarter.
def _order_moves_by_goal(state, player, moves):
    pawn_moves = []                                  # Stores pawn moves with their scores
    wall_moves = []                                  # Stores wall moves separately
    
    opponent = 2 if player == 1 else 1
    curr_opp_dist = get_shortest_path_distance(state, opponent)                                

    for move in moves:
        if move["type"] == "pawn":
            new_state = apply_move(state, move)   # Apply move on copied state
            
            # TRUE PATH SORTING
            # Smaller distance = better move
            distance_to_goal = get_shortest_path_distance(new_state, player) 
            
            # Store move with score based on distance to goal
            # Negative value is used because: smaller distance should become larger score
            pawn_moves.append((move, -distance_to_goal)) 
            
        else:
            new_state = apply_move(state, move)
            new_opp_dist = get_shortest_path_distance(new_state, opponent)
            delay = new_opp_dist - curr_opp_dist
            
            # STRICT WALL PRUNING
            if delay > 0:
                wall_moves.append((move, delay)) 

    # Sort pawn moves by score (closer to goal first)
    pawn_moves.sort(key=lambda x: x[1], reverse=True) 
    # Sort wall moves (most delay to opponent first)
    wall_moves.sort(key=lambda x: x[1], reverse=True)
                   
    # Return ordered moves: pawn moves first, then wall moves
    return [m[0] for m in pawn_moves] + [m[0] for m in wall_moves]    

# Minimax Algorithm with Alpha-Beta Pruning
def _minimax_search(state, player, depth=5, prev_pos=None): 
    
    # Recursive Minimax function with alpha-beta pruning
    def minimax_recursive(state, depth, maximizing, alpha, beta):  
        # Stop searching if depth reached 0 or someone already won
        if depth == 0 or state.winner:                             
            return evaluate_state(state, player, "hard")                   

        # Determine whose turn it is
        # maximizing = AI turn, minimizing = opponent turn
        current_player = player if maximizing else (2 if player == 1 else 1)  
        
        # Generate all possible moves for current player
        moves = generate_moves(state, current_player, allow_walls=True)        

        # If no moves available, evaluate state immediately
        if not moves:                                                       
            return evaluate_state(state, player, "hard")

        # Order moves to prioritize those that move pawn closer to goal
        ordered_moves = _order_moves_by_goal(state, current_player, moves) 

        # Prune bad walls - only need to check the top 2-5 moves (Beam Search)
        if depth == 4:
            beam_width = 5
        elif depth == 3:
            beam_width = 3
        elif depth == 2:
            beam_width = 2
        elif depth == 1:
            beam_width = 2
        else:
            beam_width = 8 
            
        ordered_moves = ordered_moves[:beam_width] 

        if maximizing: 
            max_eval = -math.inf           # Initialize max evaluation score for maximizer
            for move in ordered_moves:     # For each move, apply it and continue searching deeper
                new_state = apply_move(state, move)
                evaluation = minimax_recursive(new_state, depth - 1, False, alpha, beta)    # Get evaluation score from deeper search
                max_eval = max(max_eval, evaluation)                    # Update max evaluation score
                alpha = max(alpha, evaluation)                          # Update alpha with best score found so far for maximizer
                
                # If beta <= alpha: no need to search more branches
                if beta <= alpha:                                       
                    break
            return max_eval
        else:
            min_eval = math.inf                        # Initialize min evaluation score for minimizer
            for move in ordered_moves:
                new_state = apply_move(state, move)
                evaluation = minimax_recursive(new_state, depth - 1, True, alpha, beta)  # Get evaluation score from deeper search
                min_eval = min(min_eval, evaluation)                 # Update min evaluation score
                beta = min(beta, evaluation)                         # Beta = best score minimizer can guarantee
                
                # Stop searching unnecessary branches
                if beta <= alpha:                                    
                    break
            return min_eval

    # ROOT LEVEL SEARCH
    moves = generate_moves(state, player, allow_walls=True)
    if not moves:
        return None

    ordered_moves = _order_moves_by_goal(state, player, moves)
    ordered_moves = ordered_moves[:8] 

    best_move = None        
    best_score = -math.inf       # Initialize best score for maximizer
    alpha = -math.inf            # Initialize alpha for alpha-beta pruning
    beta = math.inf              # Initialize beta for alpha-beta pruning

    curr_dist = get_shortest_path_distance(state, player)

    for move in ordered_moves:
        new_state = apply_move(state, move)
        score = minimax_recursive(new_state, depth, False, alpha, beta)     # Get evaluation score for this move using Minimax search

        # anti backtrack penalty
        if prev_pos and move['type'] == 'pawn' and move['pos'] == prev_pos:
            score -= 300 
            
        # SHORTEST PATH ENFORCING
        if move['type'] == 'pawn':
            new_dist = get_shortest_path_distance(new_state, player)
            if new_dist > curr_dist:
                score -= 50000 

        # If this move has a better score than the best found so far, update best score and best move
        if score > best_score:  
            best_score = score   
            best_move = move

        alpha = max(alpha, score)  # Update alpha with best score found so far for maximizer

    return best_move

# Main function to get AI move based on difficulty level
def get_ai_move(state, player, ai_type): 
    global _AI_HISTORY
    
    current_pos = state.positions[player]
    prev_pos = _AI_HISTORY[player]
    
    moves = generate_moves(state, player, allow_walls=True)   

    if not moves:
        return None

    # Easy AI: mostly random with some smart pawn moves and occasional wall placements
    if ai_type == "easy":                   
        best_move = _get_easy_move(state, player, moves)
    # Medium AI: smart evaluation with moderate wall strategy and some randomness
    elif ai_type == "medium":               
        best_move = _get_medium_move(state, player, moves)
    # Hard AI: deeper Minimax search with alpha-beta pruning, move ordering, and beam search
    elif ai_type == "hard":                 
        best_move = _minimax_search(state, player, depth=5, prev_pos=prev_pos)
    else:
        best_move = random.choice(moves)
        
    _AI_HISTORY[player] = current_pos
    
    return best_move


def _get_easy_move(state, player, moves):
    pawn_moves = [m for m in moves if m["type"] == "pawn"]
    wall_moves = [m for m in moves if m["type"] == "wall"]

    # 1. Novice AI doesn't blunder randomly, so we remove the 20% random choice.
    
    # 2. Occasional wall placement (10% chance)
    # It will only place a wall if it is a random valid one, 
    # but it won't spam them like it did before.
    if wall_moves and random.random() < 0.10:
        return random.choice(wall_moves)

    # 3. Smart pawn movement toward goal
    # This remains the same, so the AI is always moving toward the win.
    if pawn_moves:
        best_pawn_moves = []            # Store best pawn moves based on shortest path distance to goal
        min_distance = float('inf')     # Initialize minimum distance to goal as infinity

        for move in pawn_moves: 
            next_state = apply_move(state, move)
            dist = get_shortest_path_distance(next_state, player) # Get distance to goal after making this move

            # If this move results in a shorter distance to goal, update minimum distance and reset best moves list
            if dist < min_distance:              
                min_distance = dist              
                best_pawn_moves = [move]
            # If this move has the same distance to goal as current best, add it to the list of best moves
            elif dist == min_distance:            
                best_pawn_moves.append(move)

        # If there are best pawn moves, randomly choose one of them to add some variability to the AI's behavior
        if best_pawn_moves:                         
            return random.choice(best_pawn_moves)

    return random.choice(moves)


def _get_medium_move(state, player, moves):
    scored_moves = []

    for move in moves:
        new_state = apply_move(state, move)
        # ----------------------------------------------------
        # RESTORED: Uses the original medium math function!
        # ----------------------------------------------------
        score = evaluate_state(new_state, player, "medium")

        # Moderate wall strategy
        if move["type"] == "wall":
            score += 8

        # Store moves with their scores based on evaluation function and wall strategy
        scored_moves.append((score, move))      

    # Sort moves by score in descending order (higher score = better move)
    scored_moves.sort(reverse=True, key=lambda x: x[0])         

    # 15% randomness from top 3 moves
    if random.random() < 0.15 and len(scored_moves) > 2:
        return random.choice(scored_moves[:3])[1]

    return scored_moves[0][1]