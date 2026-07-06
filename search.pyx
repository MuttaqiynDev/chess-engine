import chess
import chess.polyglot
import os
from evaluate import evaluate
from quiescence import quiescence_search
from ordering import order_moves

BOOK_PATH = os.path.join(os.path.dirname(__file__), "data", "komodo.bin")

# Transposition Table: stores {zobrist_hash: (depth, flag, score, best_move)}
# flags: 0 = EXACT, 1 = ALPHA (upperbound), 2 = BETA (lowerbound)
cdef dict TT = {}

cdef tuple negamax(board, int depth, int alpha, int beta):
    cdef int original_alpha = alpha
    cdef int hash_key = chess.polyglot.zobrist_hash(board)
    
    # 1. Transposition Table Lookup
    if hash_key in TT:
        tt_depth, tt_flag, tt_score, tt_move = TT[hash_key]
        if tt_depth >= depth:
            if tt_flag == 0: # EXACT
                return tt_score, tt_move
            elif tt_flag == 1: # ALPHA
                alpha = max(alpha, tt_score)
            elif tt_flag == 2: # BETA
                beta = min(beta, tt_score)
                
            if alpha >= beta:
                return tt_score, tt_move

    if board.is_game_over():
        return evaluate(board), None
        
    if depth == 0:
        return quiescence_search(board, alpha, beta), None
        
    # 2. Null Move Pruning
    # If we skip a turn and the opponent STILL can't break our beta score,
    # the position is too good and we can cut this branch immediately.
    if depth >= 3 and not board.is_check():
        board.push(chess.Move.null())
        val, _ = negamax(board, depth - 1 - 2, -beta, -beta + 1)
        val = -val
        board.pop()
        if val >= beta:
            return beta, None

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
            
    # 3. Transposition Table Store
    cdef int flag
    if best_val <= original_alpha:
        flag = 1 # ALPHA
    elif best_val >= beta:
        flag = 2 # BETA
    else:
        flag = 0 # EXACT
        
    TT[hash_key] = (depth, flag, best_val, best_move)
            
    return best_val, best_move

cpdef get_best_move(board, int depth=4):
    global TT
    # Prevent memory bloat from previous deep searches
    if len(TT) > 2000000:
        TT.clear()
        
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
