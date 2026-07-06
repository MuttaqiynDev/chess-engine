import chess

cdef dict piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 100
}

def order_moves(board, moves):
    cdef list scored_moves = []
    cdef int score
    cdef int victim_val
    cdef int attacker_val
    
    for move in moves:
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            if not victim:
                victim_val = piece_values[chess.PAWN]
            else:
                victim_val = piece_values.get(victim.piece_type, 0)
                
            attacker_val = piece_values.get(attacker.piece_type, 0) if attacker else 1
            score += 10 * victim_val - attacker_val
            
        if move.promotion:
            score += piece_values.get(move.promotion, 0)
            
        scored_moves.append((score, move))
        
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in scored_moves]
