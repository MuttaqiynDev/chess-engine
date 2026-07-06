import chess
import chess.polyglot
import os
from evaluate import evaluate
from quiescence import quiescence_search
from ordering import order_moves

BOOK_PATH = os.path.join(os.path.dirname(__file__), "data", "komodo.bin")

def negamax(board, depth, alpha, beta):
    if board.is_game_over():
        return evaluate(board), None
        
    if depth == 0:
        return quiescence_search(board, alpha, beta), None
        
    best_val = -999999
    best_move = None
    
    # Move ordering
    moves = order_moves(board, board.legal_moves)
    
    for move in moves:
        board.push(move)
        val, _ = negamax(board, depth - 1, -beta, -alpha)
        val = -val
        board.pop()
        
        if val > best_val:
            best_val = val
            best_move = move
            
        alpha = max(alpha, best_val)
        if alpha >= beta:
            break
            
    return best_val, best_move

def get_best_move(board, depth=4):
    """Returns the best move found within the given depth."""
    # 1. Consult the Opening Book first
    if os.path.exists(BOOK_PATH):
        try:
            with chess.polyglot.open_reader(BOOK_PATH) as reader:
                entry = reader.weighted_choice(board)
                return entry.move
        except IndexError:
            # Position not in book
            pass
        except Exception as e:
            print(f"Book error: {e}")
            
    # 2. Standard Alpha-Beta Search
    val, move = negamax(board, depth, -999999, 999999)
    return move
