import chess
import chess.polyglot
import os
from engine.evaluate import evaluate
from engine.quiescence import quiescence_search
from engine.ordering import order_moves

BOOK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "komodo.bin")

# Transposition Table: stores {zobrist_hash: (depth, flag, score, best_move)}
# flags: 0 = EXACT, 1 = ALPHA (upperbound), 2 = BETA (lowerbound)
cdef dict TT = {}

cdef tuple negamax(board, int depth, int alpha, int beta):
    cdef int original_alpha = alpha
    cdef unsigned long long hash_key = chess.polyglot.zobrist_hash(board)
    cdef int best_val = -999999
    cdef int val
    cdef int flag
    cdef bint last_was_null = False
    
    if len(board.move_stack) > 0 and board.move_stack[-1] == chess.Move.null():
        last_was_null = True
        
    tt_move_for_ordering = None
    
    # 1. Transposition Table Lookup
    if hash_key in TT:
        tt_depth, tt_flag, tt_score, tt_move = TT[hash_key]
        tt_move_for_ordering = tt_move
        
        if tt_depth >= depth:
            if tt_flag == 0: # EXACT
                return tt_score, tt_move
            elif tt_flag == 1: # ALPHA
                alpha = max(alpha, tt_score)
            elif tt_flag == 2: # BETA
                beta = min(beta, tt_score)
                
            if alpha >= beta:
                return tt_score, tt_move

    if board.is_game_over() or board.can_claim_draw():
        return evaluate(board), None
        
    if depth == 0:
        return quiescence_search(board, alpha, beta), None
        
    # 2. Null Move Pruning
    if depth >= 3 and not board.is_check() and not last_was_null:
        board.push(chess.Move.null())
        val, _ = negamax(board, depth - 1 - 2, -beta, -beta + 1)
        val = -val
        board.pop()
        if val >= beta:
            return beta, None

    best_move = None
    moves = order_moves(board, board.legal_moves, tt_move_for_ordering)
    
    if not moves:
        return -999999, None
        
    # Fallback to first move in case of massive Alpha cutoffs
    best_move = moves[0]
    
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
            
    # Iterative Deepening
    best_move_overall = None
    for d in range(1, depth + 1):
        val, best_move_overall = negamax(board, d, -999999, 999999)
        
    return best_move_overall
