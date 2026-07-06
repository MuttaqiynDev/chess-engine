import chess

def order_moves(board, moves):
    """Orders moves using MVV-LVA (Most Valuable Victim - Least Valuable Attacker)."""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 100
    }
    
    def score_move(move):
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            # En passant capture
            if not victim:
                victim_val = piece_values[chess.PAWN]
            else:
                victim_val = piece_values.get(victim.piece_type, 0)
                
            attacker_val = piece_values.get(attacker.piece_type, 0) if attacker else 1
            
            # MVV-LVA logic
            score += 10 * victim_val - attacker_val
            
        if move.promotion:
            score += piece_values.get(move.promotion, 0)
            
        return score
        
    return sorted(list(moves), key=score_move, reverse=True)
