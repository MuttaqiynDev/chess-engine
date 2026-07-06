import chess
import chess.polyglot
import os
from evaluate import evaluate
from quiescence import quiescence_search
from ordering import order_moves

BOOK_PATH = os.path.join(os.path.dirname(__file__), "data", "komodo.bin")

cdef tuple negamax(board, int depth, int alpha, int beta):
    if board.is_game_over():
        return evaluate(board), None
        
    if depth == 0:
        return quiescence_search(board, alpha, beta), None
        
    cdef int best_val = -999999
    cdef int val
    best_move = None
    
    moves = order_moves(board, board.legal_moves)
    
    for move in moves:
        board.push(move)
        val, _ = negamax(board, depth - 1, -beta, -alpha)
        val = -val
        board.pop()
        
        if val > best_val:
            best_val = val
            best_move = move
            
        if best_val > alpha:
            alpha = best_val
            
        if alpha >= beta:
            break
            
    return best_val, best_move

cpdef get_best_move(board, int depth=4):
    if os.path.exists(BOOK_PATH):
        try:
            with chess.polyglot.open_reader(BOOK_PATH) as reader:
                entry = reader.weighted_choice(board)
                return entry.move
        except IndexError:
            pass
        except Exception as e:
            print(f"Book error: {e}")
            
    val, move = negamax(board, depth, -999999, 999999)
    return move
