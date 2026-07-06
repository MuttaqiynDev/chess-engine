import chess
from evaluate import evaluate
from quiescence import quiescence_search
from ordering import order_moves

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
    val, move = negamax(board, depth, -999999, 999999)
    return move
